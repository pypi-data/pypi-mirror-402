# rust-ok
Rust-style `Result`, `Ok`, and `Err` primitives for Python projects.

## Installation
```bash
pip install rust-ok
```

## Usage
```python
from rust_ok import Result, Ok, Err

def parse_int(raw: str) -> Result[int, str]:
    try:
        return Ok(int(raw))
    except ValueError as exc:
        return Err(str(exc))

result = parse_int("42")
print(result.unwrap_or(0))  # -> 42
```

### Formatting exception chains
```python
from rust_ok import Err, Ok, format_exception_chain

try:
    Err(ValueError("boom")).unwrap()
except Exception as exc:
    print(format_exception_chain(exc))
```

### Iterating over results
```python
from rust_ok import Err, Ok, is_ok

results = [Ok(1), Err("bad"), Ok(3)]

for res in results:
    if is_ok(res):
        print("value:", res.unwrap())
```
