# jsonframe

A tiny, opinionated helper for **consistent JSON API response frames**.

`jsonframe` standardizes how APIs return successful responses, collections, pagination metadata, and errors — without dragging in heavy specs or forcing a framework.

---

## Design goals

- Responses are always JSON objects (never top-level arrays)
- Predictable structure across services
- Minimal cognitive load for newcomers
- No `success: true` flags — HTTP status codes already exist
- Small enough to understand in one sitting

---

## Core response rules

### Success
```json
{
  "data": ...,
  "meta": { ... }
}
```

- `data` contains the business payload (object, list, scalar, or `null`)
- `meta` contains non-business metadata (optional, always an object). Typical examples include pagination info, request IDs, timing data, or feature flags — never domain data.

### Error
```json
{
  "detail": "Invalid request payload"
}
```

Or structured:
```json
{
  "detail": {
    "error": {
      "code": "validation_error",
      "message": "Invalid request payload"
    },
    "meta": { ... }
  }
}
```

- Errors are represented by a **single error object** (no arrays, no partial failures)
- HTTP status code communicates severity
- `meta` is optional and always an object when present
- Additional fields may be included for diagnostics (e.g. `context`)

---

## Examples

#### Example of success payload and framed result
Given the user object and request_id:
```python
from jsonframe import ok

user = {
  "id": 42, 
  "name": "Ada Lovelace", 
  "email": "ada@example.com", 
  "role": "admin"
}
meta={"request_id": "req_123"}

return ok(data=user, meta=meta)
```

Result:
```json
{
  "data": {
    "id": 42,
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "role": "admin"
  },
  "meta": {
    "request_id": "req_123"
  }
}
```

#### Example error response (string)
```python
from jsonframe import error

return error(message="User not found")
```

```json
{
  "detail": "User not found"
}
```

#### Example error response (structured)
```python
from jsonframe import error

return error(
    code="not_found",
    message="User not found",
    context={"user_id": 42},
    meta={"request_id": "req_123"},
)
```

```json
{
  "detail": {
    "error": {
      "code": "not_found",
      "message": "User not found",
      "context": {
        "user_id": 42
      }
    },
    "meta": {
      "request_id": "req_123"
    }
  }
}
```

---

## Installation

### Core package
```bash
uv add jsonframe
```

Core dependency:
- `pydantic >= 2.0` (used for lightweight validation and serialization)

---

### Optional FastAPI integration

FastAPI helpers are **optional** and not installed by default.
FastAPI wraps error payloads under `detail`; `http_error()` applies this automatically without changing the core error shape.

```bash
uv add "jsonframe[fastapi]"
```

This installs:
- `fastapi`
- `starlette`

---

## Usage

### Success response
```python
from jsonframe import ok

return ok(data={"id": 1, "name": "Ada"})
```

### Empty success
```python
from jsonframe import ok

return ok()
```

### List response
```python
from jsonframe import ok

return ok(data=[{"id": 1}, {"id": 2}])
```

### Paginated list
```python
from jsonframe import ok_paged

return ok_paged(
    data=[{"id": 1}, {"id": 2}],
    total=120,
    limit=20,
    offset=40,
)
```

Result:
```json
{
  "data": [...],
  "meta": {
    "page": {
      "total": 120,
      "limit": 20,
      "offset": 40
    }
  }
}
```

---

### Error response
```python
from jsonframe import error

return error(
    code="validation_error",
    message="Invalid input",
    context={"field": "email"},
)
```

---

## FastAPI helpers (optional)

Typical imports:
```python
from jsonframe.fastapi import ok, http_error
# or
from jsonframe.fastapi import ok, ok_paged, http_error
```

### Returning framed JSON
`ok()` and `ok_paged()` return plain JSON-serializable `dict` values that you can return directly.
```python
from jsonframe.fastapi import ok, ok_paged

return ok(data={"id": 1})
```

```python
from jsonframe.fastapi import ok_paged

return ok_paged(
    data=[{"id": 1}, {"id": 2}],
    total=120,
    limit=20,
    offset=40,
)
```

### Raising framed HTTP errors
```python
from jsonframe.fastapi import http_error

raise http_error(
    404,
    code="not_found",
    message="User not found",
    context={"user_id": 42},
)
```

---

## What jsonframe is *not*

- Not a full JSON:API implementation
- Not a validation framework
- Not a transport abstraction
- Not a replacement for OpenAPI or HTTP semantics

---

## When to use jsonframe

- Internal APIs
- BFFs
- Microservices
- AI / LLM-backed services
- Teams that want consistency without ceremony

---

## Philosophy

`jsonframe` is intentionally small.

It standardizes **structure**, not **business logic**.  
If you can’t explain your API responses by pointing to this README, the library is doing too much.

---

## License

MIT
