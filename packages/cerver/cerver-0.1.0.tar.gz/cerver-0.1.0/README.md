# Cerver Python SDK

Sandboxed code execution for AI agents.

## Installation

```bash
pip install cerver
```

## Quick Start

```python
from cerver import Sandbox

# Set your API key
# export CERVER_API_KEY=sk_live_...

with Sandbox() as sandbox:
    result = sandbox.run("print('Hello from sandbox!')")
    print(result.output)  # Hello from sandbox!
```

## Usage

### Basic Execution

```python
from cerver import Sandbox

with Sandbox() as sandbox:
    # Run code
    result = sandbox.run("x = 1 + 1; print(x)")
    print(result.output)  # 2
    print(result.exit_code)  # 0
    print(result.duration)  # execution time in ms
```

### State Persistence

Variables persist across runs in the same sandbox:

```python
with Sandbox() as sandbox:
    sandbox.run("x = 10")
    sandbox.run("y = 20")
    result = sandbox.run("print(x + y)")
    print(result.output)  # 30
```

### Error Handling

```python
from cerver import Sandbox, CerverError, TimeoutError

try:
    with Sandbox() as sandbox:
        result = sandbox.run("print(undefined_var)")
        if result.exit_code != 0:
            print(f"Error: {result.error}")
except TimeoutError:
    print("Code timed out")
except CerverError as e:
    print(f"Error: {e}")
```

### Custom Configuration

```python
sandbox = Sandbox(
    api_key="sk_live_...",  # Or use CERVER_API_KEY env var
    timeout=60  # Default timeout in seconds
)
```

## API Reference

### `Sandbox`

- `run(code, timeout=None)` - Execute Python code
- `close()` - Close the sandbox

### `ExecutionResult`

- `output` - stdout as string
- `error` - stderr as string
- `exit_code` - Process exit code (0 = success)
- `duration` - Execution time in milliseconds

## License

MIT
