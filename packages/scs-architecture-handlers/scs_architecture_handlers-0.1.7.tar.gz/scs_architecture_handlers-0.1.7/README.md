# Architecture Handlers

A minimal, extensible base class for building handler components that accept inputs, optionally perform network requests, and publish results via a thread-safe queue. The same class exposes async wrappers so we only need to maintain one implementation.

## Features
- Threaded processing loop reading from an input queue and writing to a result queue
- Pluggable callback `generate_results(item, extra)` or provide `generate_results_callback` in config
- Template methods for easy adaptation: `validate_item`, `preprocess_item`, `postprocess_result`
- Optional type checking / custom validation
- Dropping policy when queues are full (with warnings & counters)
- Runtime timestamps and counters (processed/dropped/errors/network errors)
- Async wrappers (`async_feed`, `async_get_result`, `async_generate`, `async_start`, `async_cleanup`) built on the same sync core
- Hook methods for instrumentation: before/after feed, generate, network call, result retrieval, errors
- Non-blocking external callbacks: a dedicated callback worker thread is available to run user callbacks off the hot path (see “Callbacks”)

## Install / Use

---
## Install from PyPI
you can install and import the project like this:

```bash
pip install scs-architecture-handlers
```

```python
from base_handler import ArchitectureHandler
```

### Releasing to PyPI via GitLab CI
- Create a Git tag and push it; the CI pipeline builds and uploads the package:

```bash
git tag v0.1.0
git push origin v0.1.0
```

- In GitLab CI/CD settings, define a masked variable `PYPI_TOKEN` with your PyPI token. The deploy job uses Twine with `__token__` and `TWINE_PASSWORD=$PYPI_TOKEN`.

---
## Three common setups
Below are focused, copy‑pasteable examples for direct generation, callbacks & non‑blocking execution, and async generation.

### 1) Direct synchronous generation
Subclass `ArchitectureHandler` and override `generate_results`.

```python
from base_handler import ArchitectureHandler

class EchoHandler(ArchitectureHandler):
    def generate_results(self, item, extra):
        # Your core logic here (ML inference, transformation, etc.)
        return {"echo": item, "meta": extra}

h = EchoHandler(run_as_thread=False)  # no queues/threads needed for direct generate
out = h.generate("hello", tag=1)
print(out)  # {"echo": "hello", "meta": {"tag": 1}}

h.cleanup()
```

### 2) Callbacks & non‑blocking execution
Run slow user callbacks without blocking the main processing path by scheduling them on the handler’s dedicated callback thread via `_emit_async_callback`. You still pass your user callback through `generate_results_callback`.

```python
import time
from base_handler import ArchitectureHandler

# 1) Define a user callback (could be slow/heavy)
def on_result(item, extra):
    # Simulate heavy work (db write, network, etc.)
    time.sleep(0.1)
    print("callback got:", item)

# 2) Subclass and schedule the callback asynchronously from generate_results
class NonBlockingHandler(ArchitectureHandler):
    def generate_results(self, item, extra):
        result = {"value": str(item).upper(), "extra": extra}
        # Schedule user callback without blocking this call
        self._emit_async_callback(result, extra)
        return result

# 3) Use it — callbacks run on a dedicated thread and won’t stall generate()
h = NonBlockingHandler(
    run_as_thread=False,
    disable_thread=False,           # enable the sidecar callback thread
    generate_results_callback=on_result,
    callback_queue_size=8,          # tune callback backpressure as needed
)

start = time.time()
for i in range(5):
    out = h.generate(f"msg-{i}")      # returns immediately
    assert out["value"] == f"MSG-{i}"  # core logic result is available right away
elapsed = time.time() - start
print(f"generated 5 items in {elapsed:.3f}s (callbacks running in background)")

# Give callbacks a moment to drain (optional)
time.sleep(0.5)
h.cleanup()
```

Notes
- If the callback queue fills (bounded by `callback_queue_size`), new callback tasks are dropped and `dropped_count` increases; processing continues.
- For producer-style handlers that generate items on their own (e.g., microphone/STT), use `_emit_async_callback` inside that production path to keep the producer responsive.

### 3) Async generation
All public sync methods have async wrappers that run on threads under the hood.

```python
import asyncio
from base_handler import ArchitectureHandler

class EchoHandler(ArchitectureHandler):
    def generate_results(self, item, extra):
        return {"echo": item}

async def main():
    h = EchoHandler(run_as_thread=False)
    out = await h.async_generate("async-hello")
    print(out)  # {"echo": "async-hello"}
    await h.async_cleanup()

asyncio.run(main())
```

---
## Threaded pipeline example (optional)
Use the internal worker thread to consume items from an input queue and push processed results to a result queue:

```python
import time
from base_handler import ArchitectureHandler

class Doubler(ArchitectureHandler):
    def generate_results(self, item, extra):
        return item * 2

h = Doubler(run_as_thread=True, disable_thread=False)
h.feed(10)
print(h.get_result(timeout=1.0))  # 20
h.cleanup()
```

---
## Callbacks & non‑blocking execution
By default, providing `generate_results_callback` makes `generate()` call the callback inline and return its result immediately. For producer‑style handlers (for example microphone‑based STT) or advanced subclasses, you can emit callbacks asynchronously so slow callbacks don’t block processing.

- The base class exposes a dedicated, bounded callback queue and a single callback worker thread.
- Subclasses can schedule work onto this thread using the protected helper `_emit_async_callback(result, extra)`.
- If the callback queue is full, the task is dropped (and `dropped_count` is incremented) but processing continues.

Example (inside a subclass):

```python
class ProducerHandler(ArchitectureHandler):
    def generate_results(self, item, extra):
        result = heavy_compute(item)
        self._emit_async_callback(result, extra)  # schedule user callback non‑blocking
        return result
```

If you rely on async callbacks, you can tune capacity via `callback_queue_size`.

---
## Configuration keys
- `host`, `port`, `auth`: optional network settings
- `run_as_thread`: start internal worker threads (default True)
- `disable_thread`: force-disable threading even if `run_as_thread` is True
- `max_queue_size`: capacity for input queue (default 128)
- `result_queue_size`: capacity for result queue (default = `max_queue_size`)
- `verbose`: enable more logs
- `expected_type`: type or tuple for basic validation (used by default `validate_item`)
- `generate_results_callback`: alternative to subclassing `generate_results`
- `network_timeout`, `client_id_prefix`: optional settings
- `callback_queue_size`: capacity for the async callback queue (default 128); used when scheduling callbacks with `_emit_async_callback`

---
## Extension Points
To adapt the handler (e.g., Face Recognition, Gesture Generation), override these methods:

| Method | Purpose |
| ------ | ------- |
| `validate_item(item, extra)` | Return False to drop invalid items early (shape/content/type). |
| `preprocess_item(item, extra)` | Normalize or transform raw input before `generate_results`. |
| `generate_results(item, extra)` | Core computation (required unless callback supplied). |
| `postprocess_result(item, extra, result)` | Final transformation (e.g., map indices to labels). |
| `_prepare_request_payload(item, extra)` | Build structured payload for network I/O. |
| `_perform_request(payload)` | Implement actual network request (HTTP, gRPC, etc.). Call via `perform_request`. |

Instrumentation / Hooks (optional override):
- `_hook_before_feed`, `_hook_after_feed`
- `_hook_before_generate`, `_hook_after_generate`
- `_hook_before_network_call`, `_hook_after_network_call`
- `_hook_after_result`
- `_hook_on_error` (generation errors)
- `_hook_network_error` (network failures)

Counters available via `stats()`:
- processed_count, dropped_count, error_count, network_error_count

---
## Retrieving Stats
```python
stats = handler.stats()
print(stats["processed_count"], stats["dropped_count"])  # etc.
```

## Dependencies

On Debian/Ubuntu you may need:

```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev
```

## License
MIT
