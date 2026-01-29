"""Simple type checker."""

from __future__ import annotations

import typing
from types import UnionType
from typing import Literal, TypeVar, cast, get_args, get_origin, overload

T = TypeVar("T")


def is_type(obj: object, tp: object) -> bool:
    """Boolean predicate variant (handy for simple ifs).

    Return True if `obj` matches the runtime semantics of the type annotation `tp`.

    This is intended for basic runtime validation of typing constructs such as:
    - `X | Y` / `typing.Union[X, Y]`
    - `typing.Literal[...]`
    - `list[T]`, `set[T]`, `dict[K, V]`, `tuple[...]`

    Note:
        This function uses custom matching rules (e.g. treating `bool` as not matching `int`)
        and therefore may differ from plain `isinstance()` for some types.
    """
    return _matches(obj, tp)


@overload
def checked(obj: object, tp: type[T]) -> T | None: ...
@overload
def checked(obj: object, tp: object) -> object | None: ...


def checked(obj: object, tp: object) -> object | None:
    """Return `obj` typed as `T` if it matches `tp`, otherwise return `None`.

    This is a convenience wrapper around `is_type()` / `_matches()` that enables a
    common "validate then use" flow without raising exceptions.

    Example:
        `value = checked(data.get("age"), int)`

        or

        if (ret := checked(d, int)) is not None:
            ...

    Args:
        obj: Value to validate.
        tp: Target type annotation to validate against.

    Returns:
        The original object if it matches, otherwise `None`.
    """
    if _matches(obj, tp):
        return obj
    return None


@overload
def checked_or(obj: object, tp: type[T], default: T) -> T: ...
@overload
def checked_or(obj: object, tp: object, default: T) -> T: ...


def checked_or(obj: object, tp: object, default: T) -> T:
    """Return `obj` typed as `T` if it matches `tp` otherwise return `default`.

    This is a convenience wrapper around `is_type()` / `_matches()` that enables a
    common "validate then use" flow without raising exceptions.

    Example:
        `value = checked(data.get("age"), int, 10)`

    Args:
        obj: Value to validate.
        tp: Target type annotation to validate against.
        default: default value if validation fails

    Returns:
        The original object if it matches, otherwise `default`.
    """
    ret = checked(obj, tp)
    return default if ret is None else cast(T, ret)


def _matches(obj: object, tp: object) -> bool:
    """Internal recursive matcher implementing runtime checks for typing annotations.

    Supported constructs:
    - `Any` (always matches)
    - `X | Y` / `typing.Union[X, Y]`
    - `Literal[...]`
    - `list[T]`, `set[T]`, `dict[K, V]`
    - `tuple[T, ...]` and fixed-length `tuple[T1, T2, ...]`
    - Fallback to `isinstance(obj, tp)` where possible

    Special-case behavior:
        - `bool` does not match `int` even though `isinstance(True, int)` is True.

    Args:
        obj: Value to test.
        tp: Type annotation (or runtime type) to match against.

    Returns:
        True if `obj` matches `tp`, otherwise False.
    """
    if tp is typing.Any:
        return True

    # bool is subclass of int, treat it as non-int-value
    if tp is int and isinstance(obj, bool):
        return False

    origin = get_origin(tp)
    args_t = cast(tuple[object, ...], get_args(tp))

    # Union / X | Y
    if origin in (UnionType,):
        return any(_matches(obj, a) for a in args_t)

    if str(origin) == "typing.Union":
        return any(_matches(obj, a) for a in args_t)

    # Literal
    if origin is Literal:
        return any(obj == lit and type(obj) is type(lit) for lit in args_t)

    # list[T]
    if origin is list:
        if not isinstance(obj, list):
            return False
        lst = cast(list[object], obj)
        list_elem_t = args_t[0] if args_t else typing.Any
        return all(_matches(x, list_elem_t) for x in lst)

    # set[T]
    if origin is set:
        if not isinstance(obj, set):
            return False
        st = cast(set[object], obj)
        set_elem_t: object = args_t[0] if args_t else typing.Any
        return all(_matches(x, set_elem_t) for x in st)

    # frozenset
    if origin is frozenset:
        if not isinstance(obj, frozenset):
            return False
        fs = cast(frozenset[object], obj)
        f_elem_t = args_t[0] if args_t else typing.Any
        return all(_matches(x, f_elem_t) for x in fs)

    # dict[K, V]
    if origin is dict:
        if not isinstance(obj, dict):
            return False
        dct = cast(dict[object, object], obj)
        key_t: object = args_t[0] if len(args_t) > 0 else typing.Any
        val_t: object = args_t[1] if len(args_t) > 1 else typing.Any
        return all(_matches(k, key_t) and _matches(v, val_t) for k, v in dct.items())

    # tuple[T, ...] / tuple[T1, T2]
    if origin is tuple:
        if not isinstance(obj, tuple):
            return False
        tup = cast(tuple[object, ...], obj)
        if not args_t:
            return True
        if len(args_t) == 2 and args_t[1] is Ellipsis:
            return all(_matches(x, args_t[0]) for x in tup)
        return len(tup) == len(args_t) and all(
            _matches(x, t) for x, t in zip(tup, args_t, strict=True)
        )

    # fallback: runtime type
    try:
        return isinstance(obj, tp)  # pyright: ignore[reportArgumentType]
    except TypeError:
        return False
