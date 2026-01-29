from __future__ import annotations

from typing import Union

from py_typecheck import checked, is_type


def test_union_pep604_basic():
    assert is_type(1, int | str) is True
    assert is_type("x", int | str) is True
    assert is_type(1.5, int | str) is False

    assert checked(1, int | str) == 1
    assert checked("x", int | str) == "x"
    assert checked(1.5, int | str) is None


def test_union_typing_union_basic():
    tp = Union[int, str]  # noqa: UP007
    assert is_type(1, tp) is True
    assert is_type("x", tp) is True
    assert is_type(1.5, tp) is False


def test_union_nested():
    tp = int | (str | None)
    assert is_type(1, tp) is True
    assert is_type("x", tp) is True
    assert is_type(None, tp) is True
    assert is_type(1.5, tp) is False


def test_union_inside_container():
    tp = list[int | str]
    assert is_type([1, "x", 2], tp) is True
    assert is_type([1, 2, 3], tp) is True
    assert is_type(["x", object()], tp) is False


def test_union_respects_bool_is_not_int_rule():
    assert is_type(True, int | str) is False
    assert checked(True, int | str) is None
