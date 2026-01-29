"""Ollama chat helper.

This module provides :class:`OllamaChatAgent`, a thin wrapper around ``ollama.Client``
that keeps conversation history automatically.

Design goals:
- Easy to point at remote/network Ollama (host + headers).
- Automatic history (previous messages are always sent).
- Predictable request building with per-call overrides.
- Test-friendly (client dependency injection).
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Literal, Optional, Sequence, Tuple, Union


try:
    from ollama import Client  # type: ignore
except Exception:  # pragma: no cover
    Client = None  # type: ignore


Role = Literal["system", "user", "assistant", "tool"]
Message = Dict[str, Any]


class OllamaChatAgentError(RuntimeError):
    """Base error for this helper."""


class OllamaInvalidRequestError(OllamaChatAgentError):
    """Raised when the request can't be built from provided inputs."""


class OllamaConnectionError(OllamaChatAgentError):
    """Raised when the Ollama server can't be reached."""


class OllamaResponseError(OllamaChatAgentError):
    """Raised for server-side or protocol errors returned by Ollama."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, raw: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.raw = raw


@dataclass(frozen=True)
class ChatResult:
    """Normalized response from a non-streaming chat call."""

    content: str
    raw: Any


def _ensure_scheme(host: str) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"http://{host}"


def _merge_dicts(base: Optional[Dict[str, Any]], override: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if base is None and override is None:
        return None
    merged: Dict[str, Any] = dict(base or {})
    merged.update(override or {})
    return merged


class OllamaChatAgent:
    """Stateful chat session against an Ollama server.

    Notes
    -----
    - ``system`` is kept separately and automatically prepended at send-time.
    - ``history`` stores only user/assistant/tool turns (not the system prompt).
    - By default, tool calls (if any) are surfaced in ``raw``; this helper does not auto-execute tools.
    """

    SCHEMA_VERSION = 1

    def __init__(
        self,
        *,
        model: str,
        system: Optional[str] = None,
        host: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[Union[float, str]] = None,
        default_stream: bool = False,
        history: Optional[List[Message]] = None,
        max_history_messages: Optional[int] = None,
        client: Any = None,
    ) -> None:
        if not model:
            raise OllamaInvalidRequestError("model must be a non-empty string")

        self.model = model
        self.system = system
        self.host = _ensure_scheme(host) if host else None
        self.headers = dict(headers or {}) if headers else None
        self.options = dict(options or {}) if options else None
        self.keep_alive = keep_alive
        self.default_stream = default_stream
        self.max_history_messages = max_history_messages

        self._history: List[Message] = list(history or [])

        if client is not None:
            self._client = client
        else:
            if Client is None:
                raise OllamaChatAgentError(
                    "ollama package is not available; install dependencies or pass client= explicitly"
                )
            kwargs: Dict[str, Any] = {}
            if self.host:
                kwargs["host"] = self.host
            if self.headers:
                kwargs["headers"] = self.headers
            self._client = Client(**kwargs)

    @property
    def history(self) -> List[Message]:
        return list(self._history)

    def reset(self, history: Optional[List[Message]] = None) -> None:
        self._history = list(history or [])

    def add(
        self,
        *,
        role: Role,
        content: str,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if role not in ("system", "user", "assistant", "tool"):
            raise OllamaInvalidRequestError(f"invalid role: {role}")
        msg: Message = {"role": role, "content": content}
        if name is not None:
            msg["name"] = name
        if tool_call_id is not None:
            msg["tool_call_id"] = tool_call_id
        if extra:
            msg.update(extra)
        # system prompt is stored separately; allow add(system) but keep it in history if caller insists
        if role == "system" and self.system is None:
            self.system = content
        else:
            self._history.append(msg)

    def _trim_history(self) -> None:
        if self.max_history_messages is None:
            return
        if self.max_history_messages < 0:
            raise OllamaInvalidRequestError("max_history_messages must be >= 0")
        if len(self._history) <= self.max_history_messages:
            return
        self._history = self._history[-self.max_history_messages :]

    def _build_messages_for_send(self) -> List[Message]:
        msgs: List[Message] = []
        if self.system:
            msgs.append({"role": "system", "content": self.system})
        msgs.extend(self._history)
        return msgs

    def chat(
        self,
        user: Optional[str] = None,
        *,
        messages: Optional[Sequence[Message]] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        keep_alive: Optional[Union[float, str]] = None,
        tools: Optional[Any] = None,
        stream: Optional[bool] = None,
        format: Optional[Union[str, Dict[str, Any]]] = None,
    ) -> ChatResult:
        """Send a chat turn.

        Parameters
        ----------
        user:
            Convenience shorthand for adding a single user message.
        messages:
            Additional messages appended to history before sending.
        system:
            Per-call system prompt override (does not persist unless you set ``self.system``).
        stream:
            Streaming is currently not accumulated in this helper; use non-streaming for now.
        """

        if user is not None:
            self._history.append({"role": "user", "content": user})
        if messages:
            self._history.extend([dict(m) for m in messages])

        self._trim_history()

        send_system = system if system is not None else self.system
        send_history: List[Message] = []
        if send_system:
            send_history.append({"role": "system", "content": send_system})
        send_history.extend(self._history)

        if not send_history:
            raise OllamaInvalidRequestError("no messages to send; provide user or messages or history")

        send_stream = self.default_stream if stream is None else stream
        if send_stream:
            raise OllamaInvalidRequestError(
                "stream=True is not supported by this helper yet; set stream=False"
            )

        send_model = model or self.model
        send_options = _merge_dicts(self.options, options)
        send_keep_alive = self.keep_alive if keep_alive is None else keep_alive

        payload: Dict[str, Any] = {
            "model": send_model,
            "messages": send_history,
        }
        if send_options is not None:
            payload["options"] = send_options
        if send_keep_alive is not None:
            payload["keep_alive"] = send_keep_alive
        if tools is not None:
            payload["tools"] = tools
        if format is not None:
            payload["format"] = format

        try:
            raw = self._client.chat(**payload)
        except Exception as e:  # keep broad to avoid tight coupling to ollama's exception classes
            status_code = getattr(e, "status_code", None)
            error_text = getattr(e, "error", None) or str(e)
            if status_code is not None:
                raise OllamaResponseError(error_text, status_code=status_code, raw=e) from e
            # very rough connection heuristic
            if isinstance(e, OSError) or "Connection" in e.__class__.__name__:
                raise OllamaConnectionError(error_text) from e
            raise OllamaChatAgentError(error_text) from e

        content = self._extract_content(raw)
        if content is None:
            raise OllamaResponseError("could not extract assistant content from response", raw=raw)

        self._history.append({"role": "assistant", "content": content})
        self._trim_history()

        return ChatResult(content=content, raw=raw)

    @staticmethod
    def _extract_content(raw: Any) -> Optional[str]:
        # Most common: {'message': {'role': 'assistant', 'content': '...'}}
        if isinstance(raw, dict):
            msg = raw.get("message")
            if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                return msg.get("content")
            # sometimes response may be shaped differently
            if isinstance(raw.get("content"), str):
                return raw.get("content")
        # Some clients may return objects with attributes
        msg = getattr(raw, "message", None)
        if msg is not None:
            content = getattr(msg, "content", None)
            if isinstance(content, str):
                return content
        content = getattr(raw, "content", None)
        if isinstance(content, str):
            return content
        return None

    def save(self, path: Union[str, Path]) -> None:
        p = Path(path)
        data = {
            "schema_version": self.SCHEMA_VERSION,
            "model": self.model,
            "system": self.system,
            "options": self.options,
            "keep_alive": self.keep_alive,
            "default_stream": self.default_stream,
            "max_history_messages": self.max_history_messages,
            "history": self._history,
        }
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Union[str, Path], *, client: Any = None) -> "OllamaChatAgent":
        p = Path(path)
        data = json.loads(p.read_text())
        if not isinstance(data, dict):
            raise OllamaInvalidRequestError("invalid save file")
        if data.get("schema_version") != cls.SCHEMA_VERSION:
            raise OllamaInvalidRequestError("unsupported schema_version")
        model = data.get("model")
        if not isinstance(model, str) or not model:
            raise OllamaInvalidRequestError("save file missing model")
        system = data.get("system")
        options = data.get("options")
        keep_alive = data.get("keep_alive")
        default_stream = bool(data.get("default_stream", False))
        max_history_messages = data.get("max_history_messages")
        history = data.get("history")
        if history is None:
            history = []
        if not isinstance(history, list):
            raise OllamaInvalidRequestError("save file history must be a list")

        return cls(
            model=model,
            system=system,
            options=options,
            keep_alive=keep_alive,
            default_stream=default_stream,
            max_history_messages=max_history_messages,
            history=history,
            client=client,
        )
