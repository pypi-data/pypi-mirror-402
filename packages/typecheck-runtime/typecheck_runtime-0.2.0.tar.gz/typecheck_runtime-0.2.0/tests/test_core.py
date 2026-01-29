from __future__ import annotations

from typing import Any, Literal, Protocol

from py_typecheck import checked, checked_or, is_type


class P(Protocol):
    def foo(self) -> int: ...


class C:
    def foo(self) -> int:
        return 42


def test_fallback_isinstance_typeerror_returns_false():
    obj = C()
    tp = P

    assert is_type(obj, tp) is False
    assert checked(obj, tp) is None
    assert checked_or(obj, tp, 1) == 1


def test_fallback_isinstance_with_typing_object():
    tp = list[int]
    assert is_type([], tp) is True
    assert is_type((), tp) is False


def test_any():
    assert checked(Any, Any) is Any
    assert checked(Any, int) is None
    assert is_type(Any, Any) is True
    assert is_type(Any, int) is False


def test_bool_is_not_int():
    assert checked(True, int) is None
    assert is_type(True, int) is False


def test_int_is_not_bool():
    assert checked(1, bool) is None
    assert checked(True, bool) is True
    assert checked(False, bool) is False

    assert is_type(True, bool) is True
    assert is_type(False, bool) is True
    assert is_type(0, Literal[False]) is False
    assert is_type(0, False) is False

    assert is_type(False, bool) is True


def test_int_ok():
    assert checked(0, int) == 0
    assert checked(3, int) == 3


def test_dict_str_int():
    assert checked({"a": 1}, dict[str, int]) == {"a": 1}
    assert checked({"a": "x"}, dict[str, int]) is None


def test_nonempty_idiom():
    d: object = 0
    assert (x := checked(d, int)) is not None
    assert x == 0


def test_literal_true():
    assert checked(True, Literal[True]) is True
    assert checked(False, Literal[True]) is None
    
def test_or():
    assert checked_or("string", str, "default") == "string"
    assert checked_or(1, int, "default") == 1
    assert checked_or(1, str, "default") == "default"
