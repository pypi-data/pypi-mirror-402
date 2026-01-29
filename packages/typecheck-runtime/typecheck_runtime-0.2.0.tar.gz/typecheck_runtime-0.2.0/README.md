# typecheck-runtime 

Tiny runtime checker for typing annotations with an Option-like API.

`py-typecheck` solves a very specific problem:

**I have a value (object or Any) and I want to check if
the value refers to specific typing annotation.**

Does not parse data. Does not transforms data.
Just **checks structure and returns refered value** or 
`None` if validation failed.


## Installation

```bash
pip install typecheck-runtime

Python ≥ 3.10
```

---

## Core idea

Main function is `checked`

```python
from py_typecheck import checked
```

Acts like `Option[T]` or Rust-like `Some(T, None)`:
 - returns value if matches the type
 - returns `None` if validation failed

 No exceptions, no side-efects.

---

### Basic usage

```python
value: object = {"a": 1}

if (d := checked(value, dict[str, int])) is not None:
    print(d["a"] + 1)
```

**Important**
- always compare against `None` when using `checked`
- do not rely on truthiness (0, False, [] are valid values!)
- bool is treated as not matching int (so True wont pass as int)

---

## `checked_or`

If you want the same runtime check as `checked()`, but with a convenient fallback,
use `checked_or()`.

- returns the original value if it matches the target type
- otherwise returns the provided `default`

This is especially handy when you want a safe, typed value in one expression
without handling `None`.

```python
from py_typecheck import checked_or

age: object = "not-a-number"

# returns 10 because "not-a-number" is not an int
value = checked_or(age, int, 10)
```

Works with typing constructs the same way as `checked()`:

```python
from py_typecheck import checked_or

payload: object = {"tags": ["a", "b"]}

tags = checked_or(payload, dict[str, list[str]], {"tags": []})["tags"]
```

Important notes:
- `checked_or()` relies on `checked()` semantics (including the `bool` vs `int` rule)
- `default` should already be the correct value you want to use (no coercion happens)

---

## Supported typing constructs

`py-typecheck` supports common runtime-validable constructs from `typing`:

### Primitive types

```python
checked(1, int)          # 1
checked("x", int)        # None
checked(True, int)       # None
```
Note: bool is not considered an int in this library.


### Union (X | Y, typing.Union)

```python
checked(1, int | str)      # 1
checked("x", int | str)    # "x"
checked(1.5, int | str)    # None
```

### List / Set / FrozenSet

```python
checked([1, 2], list[int])           # [1, 2]
checked({1, 2}, set[int])            # {1, 2}
checked(frozenset({1}), frozenset[int])
```

Nested structures work as expected:
```python
checked([[1, 2], [3]], list[list[int]])
```

### Dict

```python
checked({"a": 1}, dict[str, int])
checked({"a": "x"}, dict[str, int])   # None
```

Supports unions and nesting:
```python
checked({"a": [1, 2]}, dict[str, list[int]])
```

### Tuple

Fixed-length:
```python
checked((1, "x"), tuple[int, str])
```

Variadic:
```python
checked((1, 2, 3), tuple[int, ...])
```

### Literal

```python
from typing import Literal

checked(True, Literal[True])    # True
checked(False, Literal[True])   # None
```

### Any
```python
from typing import Any

checked(object(), Any)   # always matches
```
---

## `is_type`

There is also a boolean helper:

```python
from py_typecheck import is_type

if is_type(value, dict[str, int]):
    ...
```

- It returns only True / False.
- For most code paths, checked is preferred, because it avoids
type confusion and double-checking mistakes.

---

### Design principles
- Explicit is better than clever
-	No exceptions for control flow
-	No implicit casting
-	No data mutation
-	No dependency on dataclasses or models
-	One function, one responsibility

This is not a validator framework.
This is a runtime structural check with a safe return value.

### Non-goals

`py-typecheck` intentionally does not:
-	coerce types ("1" → 1)
-	fill defaults
-	validate constraints (ranges, regexes, etc.)
-	replace pydantic or attrs

If you want parsing + validation + coercion → use `Pydantic`.
If you want “is this already the right shape?” → **use this**.

---

## Comparison

|Tool|Purpose|
|-|-|
|isinstance|Runtime type only|
|typing|Static type checking|
|pydantic|Parsing + validation + coercion|
|py-typecheck|Runtime structural check only|

---

## Development status
-	Fully typed (basedpyright strict)
-	Tested against Python 3.10 – 3.13
-	CI + lint + coverage
-	Small surface area, easy to audit

---

License
MIT

