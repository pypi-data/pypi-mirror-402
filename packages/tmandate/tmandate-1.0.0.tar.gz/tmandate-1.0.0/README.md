# TMANDATE Python SDK

## Install (Local)

```bash
pip install -e .
```

## Set API Key

```bash
export TMANDATE_API_KEY=tm_live_...
```

## Example

```python
from tmandate import authority

with authority("google.com") as permit:
    permit.step()
    print("Execution permitted")
```

## Expected Output

When you run the example, you'll see the execution permit is created and the step is tracked. The `authority()` function returns an `ExecutionPermit` object that provides execution control based on the API response.

## Note

PyPI install coming later. For now, install from source.
