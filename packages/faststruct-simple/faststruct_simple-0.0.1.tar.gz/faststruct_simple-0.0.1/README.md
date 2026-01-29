# faststruct-simple

A **simple / experimental** high-performance binary serializer for Python dicts,
implemented as a **CPython C extension**.

⚠️ This project is **not related** to Python’s built-in `struct` module.  
⚠️ The binary format and API are **not stable yet**.

## Example

```python
import faststruct

data = {"a": b"123", "b": b"456"}
payload = faststruct.serialize(data)
obj = faststruct.deserialize(payload)
