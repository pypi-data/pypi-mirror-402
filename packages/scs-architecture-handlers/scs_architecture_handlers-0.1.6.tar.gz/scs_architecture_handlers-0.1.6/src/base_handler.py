"""architecture_handler.py

Base ArchitectureHandler class providing a generalized pattern for feeding input
items, processing them (optionally via network requests), and exposing results
through a thread-safe queue. The same class is monkeypatched with asynchronous
wrappers so only one implementation must be maintained.

Key Concepts
------------
- Input Queue: Raw items fed into the handler via feed() / feedThread().
- Processing Thread: Consumes input items, invokes the generate_results() hook
  (override point) and places processed results onto the result queue.
- Result Queue: Stores processed results accessible via get_result().
- Callback Hook: generate_results(item, extra) -> Any should be overridden
  or provided via config['generate_results_callback']; otherwise a warning
  is emitted.
- Networking: _perform_request(payload) can be overridden for custom remote
  calls. Default implementation is a stub.
- Async Support: Coroutine wrappers are attached dynamically so the same class
  can be used with "await handler.async_feed(... )" etc.

Configuration Dict Keys
-----------------------
host: str                    Remote host (optional)
port: int                    Remote port (optional)
auth: Any                    Authentication token / credentials (optional)
run_as_thread: bool          Whether to start internal processing thread(s)
disable_thread: bool         If True, no internal threads are started even if
                             run_as_thread is True (safeguard)
max_queue_size: int          Maximum size for input & result queues (default 128)
verbose: bool                Enable verbose logging (INFO vs WARNING)
expected_type: type | tuple  If set, input items are type-checked on feed();
                             mismatch causes warning & drop.
generate_results_callback: Callable[[Any, dict], Any]
                             External callback alternative to overriding
                             generate_results().
result_queue_size: int       Separate size for result queue (defaults to max_queue_size)
network_timeout: float       Optional timeout for network request method.
client_id_prefix: str        Prefix for auto-generated client id.

Public Methods (Sync)
---------------------
feed(item, **extra)          Feed an item; may be dropped if queue full or type mismatch.
clear_feed()                 Clear pending input items.
get_result(timeout=None)     Retrieve processed result.
generate(item, **extra)      Direct synchronous generation (bypassing queues).
start()                      Start worker threads if configured.
cleanup()                    Stop threads and flush queues.

Public Async Wrappers (added dynamically)
----------------------------------------
async_feed(), async_get_result(), async_generate(), async_cleanup(), async_start()

Override Points
---------------
- generate_results(self, item, extra) -> Any
- _prepare_request_payload(self, item, extra) -> dict
- _perform_request(self, payload) -> Any

Threading Model
---------------
If run_as_thread is True (and not disabled), a single processing thread is
started that consumes input_queue and writes processed outputs to result_queue.
A lightweight heartbeat thread updates timestamps.

Timestamps
----------
created_at, last_feed_at, last_generate_at, last_result_at, last_network_call_at

Logging
-------
Uses the standard logging module. Verbose toggles INFO vs WARNING level.

Extension Points Summary
------------------------
Subclasses can override these template methods for adaptation:
validate_item(item, extra) -> bool            Input validation (shape/type/content)
preprocess_item(item, extra) -> (item, extra) Transform/normalize before generate_results
generate_results(item, extra) -> Any          Core processing (must override or supply callback)
postprocess_result(item, extra, result) -> Any Final transformation (e.g., decode classes)
_prepare_request_payload(item, extra) -> dict Build payload for network requests
_perform_request(payload) -> Any              Actual network I/O (override only, call via perform_request)

Hook Methods (for instrumentation/metrics):
_hook_before_feed, _hook_after_feed, _hook_before_generate, _hook_after_generate,
_hook_before_network_call, _hook_after_network_call, _hook_after_result,
_hook_on_error, _hook_network_error
"""
from __future__ import annotations

import asyncio
import queue
import threading
import time
import traceback
import uuid
import warnings
import logging
import weakref
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

# Type alias for config dict (kept for backward references, not used directly)
ConfigDict = Dict[str, Any]


class ArchitectureHandler:
    """General-purpose architecture handler base class.

    Parameters
    ----------
    host : Optional[str]
        Remote host (optional)
    port : Optional[int]
        Remote port (optional)
    auth : Any
        Authentication token / credentials (optional)
    run_as_thread : bool
        Whether to start internal processing thread(s) (default True)
    disable_thread : bool
        If True, no internal threads are started even if run_as_thread is True
    max_queue_size : int
        Maximum size for input queue (default 128)
    result_queue_size : Optional[int]
        Separate size for result queue (defaults to max_queue_size)
    verbose : bool
        Enable verbose logging (INFO vs WARNING)
    expected_type : Optional[type | tuple]
        If set, input items are type-checked on feed(); mismatch causes drop.
    network_timeout : Optional[float]
        Optional timeout for network requests (subclasses may use)
    client_id_prefix : str
        Prefix for auto-generated client id.
    generate_results_callback : Optional[Callable[[Any, dict], Any]]
        External callback alternative to overriding generate_results().
callback_queue_size : int
Max number of pending async callback tasks (default 128).
    """

    # --- Initialization ---
    def __init__(
        self,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        auth: Any = None,
        run_as_thread: bool = True,
        disable_thread: bool = False,
        max_queue_size: int = 128,
        result_queue_size: Optional[int] = None,
        verbose: bool = False,
        expected_type: Optional[Union[Type, Tuple[Type, ...]]] = None,
        network_timeout: Optional[float] = None,
        client_id_prefix: str = "client",
        generate_results_callback: Optional[Callable[[Any, Dict[str, Any]], Any]] = None,
        callback_queue_size: int = 128,
    ) -> None:
        # Basic configuration
        self.host: Optional[str] = host
        self.port: Optional[int] = port
        self.auth: Any = auth

        self.run_as_thread: bool = bool(run_as_thread)
        self.disable_thread: bool = bool(disable_thread)
        self.verbose: bool = bool(verbose)
        self.expected_type: Optional[Union[Type, Tuple[Type, ...]]] = expected_type
        self.network_timeout: Optional[float] = network_timeout

        max_q: int = int(max_queue_size)
        result_q: int = int(result_queue_size if result_queue_size is not None else max_q)

        # Logging setup
        self._logger = logging.getLogger(f"ArchitectureHandler.{id(self)}")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            handler.setFormatter(fmt)
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO if self.verbose else logging.WARNING)

        # Queues
        self.input_queue: "queue.Queue[Any]" = queue.Queue(maxsize=max_q)
        self.result_queue: "queue.Queue[Any]" = queue.Queue(maxsize=result_q)
        # Dedicated async-callback queue to avoid blocking processing
        self._callback_queue: "queue.Queue[Tuple[Any, Dict[str, Any]]]" = queue.Queue(maxsize=int(callback_queue_size))

        # Runtime state
        self.client_id_prefix: str = client_id_prefix
        self.client_id: str = f"{self.client_id_prefix}-{uuid.uuid4()}"
        self.created_at: float = time.time()
        self.last_feed_at: Optional[float] = None
        self.last_generate_at: Optional[float] = None
        self.last_result_at: Optional[float] = None
        self.last_network_call_at: Optional[float] = None
        # Counters for instrumentation
        self.processed_count: int = 0
        self.dropped_count: int = 0
        self.error_count: int = 0
        self.network_error_count: int = 0

        self.stop_event = threading.Event()
        self.processing_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.callback_thread: Optional[threading.Thread] = None
        self._cleaned: bool = False
        self._finalizer = weakref.finalize(self, ArchitectureHandler._finalize_callback, weakref.ref(self))

        # Callback injection if provided
        cb = generate_results_callback
        if cb is not None and callable(cb):
            self._external_callback: Optional[Callable[[Any, Dict[str, Any]], Any]] = cb
        else:
            self._external_callback = None
            # Warn only if the subclass did not override generate_results
            try:
                is_overridden = self.generate_results.__func__ is not ArchitectureHandler.generate_results  # type: ignore[attr-defined]
            except AttributeError:
                is_overridden = getattr(self.__class__, "generate_results", None) is not ArchitectureHandler.generate_results
            if not is_overridden:
                warnings.warn(
                    "No generate_results_callback provided and generate_results not overridden; "
                    "default implementation will raise NotImplementedError.",
                    UserWarning,
                )

        # Automatically start threads if configured
        if self.run_as_thread and not self.disable_thread:
            self.start()

    # --- Core Public API (Sync) ---
    def feed(self, item: Any, **extra: Any) -> bool:
        """Feed an item into the handler.

        Performs optional type checking. If the input queue is full the item is dropped.

        Parameters
        ----------
        item : Any
            The item to enqueue for processing.
        **extra : Any
            Additional metadata (e.g., audio features) passed through to generate_results.

        Returns
        -------
        bool
            True if enqueued, False if dropped.
        """
        # Hook before feed for monitoring
        try:
            self._hook_before_feed(item, dict(extra))
        except Exception:
            self._logger.exception("Error in _hook_before_feed")

        # Centralized validation point (subclasses override validate_item)
        if not self.validate_item(item, dict(extra)):
            self._logger.warning("Dropped item due to validation failure.")
            try:
                self._hook_after_feed(item, dict(extra), False)
            except Exception:
                self._logger.exception("Error in _hook_after_feed")
            return False

        if self.stop_event.is_set():
            self._logger.warning("Handler is stopping; feed ignored.")
            try:
                self._hook_after_feed(item, dict(extra), False)
            except Exception:
                self._logger.exception("Error in _hook_after_feed")
            return False

        try:
            # Put both item and its extra metadata so the worker can use it
            self.input_queue.put((item, dict(extra)), block=False)
            try:
                self._hook_after_feed(item, dict(extra), True)
            except Exception:
                self._logger.exception("Error in _hook_after_feed")
            return True
        except queue.Full:
            self._logger.warning("Input queue full (size=%d); item dropped.", self.input_queue.maxsize)
            try:
                self._hook_after_feed(item, dict(extra), False)
            except Exception:
                self._logger.exception("Error in _hook_after_feed")
            return False

    # Alias as specified in initial outline
    feedThread = feed  # Maintain naming from specification

    def clear_feed(self) -> int:
        """Clear all pending items from the input queue.

        Returns
        -------
        int
            Number of items removed.
        """
        removed = 0
        while True:
            try:
                self.input_queue.get_nowait()
                removed += 1
            except queue.Empty:
                break
        self._logger.info("Cleared %d pending input items.", removed)
        return removed

    def generate(self, item: Any, **extra: Any) -> Any:
        """Directly generate a result synchronously (bypassing queues).

        Updates timestamps and performs type checking similar to feed().

        Parameters
        ----------
        item : Any
            Input item.
        **extra : Any
            Additional metadata for the callback.

        Returns
        -------
        Any
            The processed result.
        """
        if not self.validate_item(item, dict(extra)):
            exp = f" expected {self.expected_type}" if self.expected_type else ""
            raise TypeError(f"Item validation failed{exp}; got {type(item)}")
        # call hook before generate
        try:
            self._hook_before_generate(item, dict(extra))
        except Exception:
            self._logger.exception("Error in _hook_before_generate")
        pre_item, pre_extra = self.preprocess_item(item, dict(extra))
        result = self.generate_results(pre_item, pre_extra)
        result = self.postprocess_result(pre_item, pre_extra, result)
        try:
            self._hook_after_generate(pre_item, pre_extra, result)
        except Exception:
            self._logger.exception("Error in _hook_after_generate")
        return result

    def get_result(self, timeout: Optional[float] = None) -> Any:
        """Retrieve the next processed result from the result queue.

        Parameters
        ----------
        timeout : float, optional
            Seconds to wait; if None, waits indefinitely.

        Returns
        -------
        Any
            The next result, or None if timeout elapses.
        """
        try:
            result = self.result_queue.get(timeout=timeout)
            try:
                self._hook_after_result(result)
            except Exception:
                self._logger.exception("Error in _hook_after_result")
            return result
        except queue.Empty:
            return None

    def start(self) -> None:
        """Start internal threads if not already running."""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        if self.disable_thread:
            self._logger.warning("Threading disabled by configuration; start() ignored.")
            return
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self._processing_loop, name=f"Proc-{self.client_id}", daemon=True)
        self.processing_thread.start()
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, name=f"Heartbeat-{self.client_id}", daemon=True)
        self.heartbeat_thread.start()
        # Start callback thread if there's an external callback defined
        if self._external_callback and (self.callback_thread is None or not self.callback_thread.is_alive()):
            self.callback_thread = threading.Thread(target=self._callback_loop, name=f"Callback-{self.client_id}", daemon=True)
            self.callback_thread.start()
            self._logger.info("Handler threads started (client_id=%s).", self.client_id)

    def cleanup(self) -> None:
        """Signal threads to stop and drain queues.

        Idempotent: safe to call multiple times.
        """
        if self._cleaned:
            return
        self._cleaned = True
        self.stop_event.set()
        if self.processing_thread:
            try:
                self.processing_thread.join(timeout=2)
            except Exception:
                traceback.print_exc()
        if self.heartbeat_thread:
            try:
                self.heartbeat_thread.join(timeout=2)
            except Exception:
                traceback.print_exc()
        if self.callback_thread:
            try:
                self.callback_thread.join(timeout=2)
            except Exception:
                traceback.print_exc()
                # Best-effort log; may be unavailable during interpreter shutdown
                try:
                    self._logger.info("Threads joined. Draining result queue if any.")
                except Exception:
                    traceback.print_exc()
                # Prevent finalizer from running again
                try:
                    if getattr(self, "_finalizer", None) and self._finalizer.alive:
                        self._finalizer.detach()
                except Exception:
                    traceback.print_exc()

    # --- Async callback worker ---
    def _ensure_callback_thread(self) -> None:
        if self.disable_thread:
            return
        if self._external_callback and (self.callback_thread is None or not self.callback_thread.is_alive()):
            # Do not set stop_event here; this is a sidecar thread
            self.callback_thread = threading.Thread(target=self._callback_loop, name=f"Callback-{self.client_id}", daemon=True)
            self.callback_thread.start()

    def _emit_async_callback(self, item: Any, extra: Dict[str, Any]) -> bool:
        """Schedule an external callback execution on a dedicated thread.
        +
        Returns True if scheduled, False if dropped (e.g., queue full or no callback set).
        """
        if not self._external_callback:
            return False
        # Lazy-start the callback thread on first use if not already started
        self._ensure_callback_thread()
        try:
            self._callback_queue.put((item, dict(extra)), block=False)
            return True
        except queue.Full:
            # Count as dropped work to surface backpressure
            self.dropped_count += 1
            self._logger.warning("Callback queue full (size=%d); callback task dropped.", self._callback_queue.maxsize)
            return False
    def _callback_loop(self) -> None:
        """Worker loop to run external callbacks without blocking processing."""
        while not self.stop_event.is_set() or not self._callback_queue.empty():
            try:
                task = self._callback_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            item, extra = task
            try:
                # Execute user-provided callback; ignore return value
                self._external_callback(item, extra)  # type: ignore[misc]
            except Exception as exc:
                # Surface callback errors through on_error hook
                self._logger.exception("Error in external callback: %s", exc)
                try:
                    self._hook_on_error(item, extra, exc)
                except Exception:
                    self._logger.exception("Error in _hook_on_error (from callback)")
            finally:
                try:
                    self._callback_queue.task_done()
                except ValueError:
                    traceback.print_exc()

    # --- Internal Thread Workers ---
    def _processing_loop(self) -> None:
        """Worker loop: consume input_queue, process items, produce results."""
        while not self.stop_event.is_set():
            try:
                # Use a short timeout so we can observe stop_event promptly
                queued = self.input_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if isinstance(queued, tuple) and len(queued) == 2 and isinstance(queued[1], dict):
                item, extra = queued
            else:
                item, extra = queued, {}
            try:
                self._hook_before_generate(item, extra)
            except Exception:
                self._logger.exception("Error in _hook_before_generate")
            try:
                pre_item, pre_extra = self.preprocess_item(item, extra)
                result = self.generate_results(pre_item, pre_extra)
                result = self.postprocess_result(pre_item, pre_extra, result)
                try:
                    self.result_queue.put(result, block=False)
                except queue.Full:
                    self._logger.warning(
                        "Result queue full (size=%d); processed result dropped.", self.result_queue.maxsize
                    )
                try:
                    self._hook_after_generate(pre_item, pre_extra, result)
                except Exception:
                    self._logger.exception("Error in _hook_after_generate")
            except Exception as exc:  # broad catch for worker safety
                self._logger.exception("Error processing item: %s", exc)
                try:
                    self._hook_on_error(item, extra, exc)
                except Exception:
                    self._logger.exception("Error in _hook_on_error")
            finally:
                try:
                    self.input_queue.task_done()
                except ValueError:
                    traceback.print_exc()

    def _heartbeat_loop(self) -> None:
        """Heartbeat thread updating timestamps (runtime information)."""
        while not self.stop_event.is_set():
            # Could update more runtime metrics here
            time.sleep(1.0)

    # --- Callback & Networking ---
    def generate_results(self, item: Any, extra: Dict[str, Any]) -> Any:  # noqa: D401 (documented above)
        """Override or provide via config to implement item processing.

        Default behavior: if an external callback is provided, delegate to it.
        Else raise NotImplementedError.
        """
        if self._external_callback is not None:
            return self._external_callback(item, extra)
        raise NotImplementedError("generate_results must be implemented by a subclass or provided as a callback")

    def _prepare_request_payload(self, item: Any, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload for a potential network request.

        Override to customize payload structure.
        """
        return {
            "client_id": self.client_id,
            "item": item,
            "extra": extra,
            "timestamp": time.time(),
        }

    def perform_request(self, payload: Dict[str, Any]) -> Any:
        """Wrapper around the overridable `_perform_request` that guarantees
        statistic hooks run before/after the actual network call. Subclasses
        should override `_perform_request(payload)` rather than this wrapper.
        """
        try:
            self._hook_before_network_call(payload)
        except Exception:
            self._logger.exception("Error in _hook_before_network_call")
        try:
            resp = self._perform_request(payload)
        except Exception as exc:
            try:
                self._hook_network_error(payload, exc)
            except Exception:
                self._logger.exception("Error in _hook_network_error")
            raise
        try:
            self._hook_after_network_call(payload, resp)
        except Exception:
            self._logger.exception("Error in _hook_after_network_call")
        return resp

    def _perform_request(self, payload: Dict[str, Any]) -> Any:
        """Perform a network request.

        Override this method to implement actual I/O (e.g., HTTP). The default
        implementation simply returns the payload.

        Note: do not update statistics here; use `perform_request` to ensure
        hooks run even when `_perform_request` is overridden.
        """
        return payload

    # --- Statistic Hooks ---
    def _hook_before_feed(self, item: Any, extra: Dict[str, Any]) -> None:
        """Hook executed before/after feed; default does nothing. Override to
        collect statistics or to integrate with monitoring systems."""
        return None

    def _hook_after_feed(self, item: Any, extra: Dict[str, Any], enqueued: bool) -> None:
        """Hook executed after feed() completes. Default updates last_feed_at
        only when an item is successfully enqueued."""
        if enqueued:
            self.last_feed_at = time.time()
            if self.verbose:
                self._logger.info("Item fed at %s", self.last_feed_at)
        else:
            self.dropped_count += 1

    def _hook_before_generate(self, item: Any, extra: Dict[str, Any]) -> None:
        """Hook executed immediately before generation begins.

        Default updates last_generate_at timestamp.
        """
        self.last_generate_at = time.time()
        if self.verbose:
            self._logger.info("Generate started at %s", self.last_generate_at)

    def _hook_after_generate(self, item: Any, extra: Dict[str, Any], result: Any) -> None:
        """Hook executed immediately after generation finishes.

        Default updates last_result_at timestamp.
        """
        self.last_result_at = time.time()
        self.processed_count += 1
        if self.verbose:
            self._logger.info("Generate finished at %s", self.last_result_at)

    def _hook_before_network_call(self, payload: Dict[str, Any]) -> None:
        """Hook executed immediately before a network call."""
        if self.verbose:
            self._logger.info("Network call starting (client=%s)", self.client_id)

    def _hook_after_network_call(self, payload: Dict[str, Any], response: Any) -> None:
        """Hook executed immediately after a network call.

        Default updates last_network_call_at timestamp.
        """
        self.last_network_call_at = time.time()
        if self.verbose:
            self._logger.info("Network call finished at %s", self.last_network_call_at)

    def _hook_after_result(self, result: Any) -> None:
        """Hook executed when a result is retrieved from the result queue.

        Default does nothing but can be overridden for monitoring.
        """
        return None

    def _hook_network_error(self, payload: Dict[str, Any], exc: BaseException) -> None:
        """Hook executed when a network call raises an exception."""
        if self.verbose:
            self._logger.error("Network error: %s", exc)
        self.network_error_count += 1

    def _hook_on_error(self, item: Any, extra: Dict[str, Any], exc: BaseException) -> None:
        """Hook executed when an error occurs during generation."""
        self.error_count += 1

    # --- Finalization helpers ---
    def _finalize_cleanup(self) -> None:
        """Finalizer-safe cleanup without logging and with short joins."""
        if self._cleaned:
            return
        self._cleaned = True
        try:
            self.stop_event.set()
        except Exception:
            return
        for th in (self.processing_thread, self.heartbeat_thread):
            try:
                if th is not None:
                    th.join(timeout=0.5)
            except Exception:
                traceback.print_exc()

    @staticmethod
    def _finalize_callback(ref: "weakref.ReferenceType[ArchitectureHandler]") -> None:
        obj = ref()
        if obj is None:
            return
        try:
            obj._finalize_cleanup()
        except Exception:
            traceback.print_exc()

    # --- Introspection Helpers ---
    def stats(self) -> Dict[str, Any]:
        """Return runtime statistics as a dictionary."""
        return {
            "client_id": self.client_id,
            "created_at": self.created_at,
            "last_feed_at": self.last_feed_at,
            "last_generate_at": self.last_generate_at,
            "last_result_at": self.last_result_at,
            "last_network_call_at": self.last_network_call_at,
            "input_queue_size": self.input_queue.qsize(),
            "result_queue_size": self.result_queue.qsize(),
            "run_as_thread": self.run_as_thread and not self.disable_thread,
            "processed_count": self.processed_count,
            "dropped_count": self.dropped_count,
            "error_count": self.error_count,
            "network_error_count": self.network_error_count,
        }

    # --- Context Manager Support ---
    def __enter__(self) -> "ArchitectureHandler":
        if self.run_as_thread and not self.disable_thread:
            self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.cleanup()

    def validate_item(self, item: Any, extra: Dict[str, Any]) -> bool:
        """Validate an input item before enqueueing / generation.

        Default implementation enforces `expected_type` if configured.
        Subclasses can override to check shapes, ranges, or mandatory keys.
        """
        if self.expected_type and not isinstance(item, self.expected_type):
            return False
        return True

    def preprocess_item(self, item: Any, extra: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """Preprocess an item/extra before generation (e.g., image normalization).

        Should return a possibly transformed (item, extra) tuple.
        """
        return item, extra

    def postprocess_result(self, item: Any, extra: Dict[str, Any], result: Any) -> Any:
        """Postprocess the raw result (e.g., decode logits -> labels)."""
        return result


# --- Async Monkeypatching ---

def _patch_async_methods(cls: type) -> None:
    """Attach asynchronous wrapper methods to the class.

    Each async method delegates to its synchronous counterpart via asyncio.to_thread,
    ensuring no duplication of core logic.
    """

    async def async_feed(self: ArchitectureHandler, item: Any, **extra: Any) -> bool:
        return await asyncio.to_thread(self.feed, item, **extra)

    async def async_get_result(self: ArchitectureHandler, timeout: Optional[float] = None) -> Any:
        return await asyncio.to_thread(self.get_result, timeout)

    async def async_generate(self: ArchitectureHandler, item: Any, **extra: Any) -> Any:
        return await asyncio.to_thread(self.generate, item, **extra)

    async def async_start(self: ArchitectureHandler) -> None:
        await asyncio.to_thread(self.start)

    async def async_cleanup(self: ArchitectureHandler) -> None:
        await asyncio.to_thread(self.cleanup)

    # Attach if not already present
    for name, fn in {
        "async_feed": async_feed,
        "async_get_result": async_get_result,
        "async_generate": async_generate,
        "async_start": async_start,
        "async_cleanup": async_cleanup,
    }.items():
        if not hasattr(cls, name):
            setattr(cls, name, fn)


_patch_async_methods(ArchitectureHandler)

__all__ = ["ArchitectureHandler", "ConfigDict"]
