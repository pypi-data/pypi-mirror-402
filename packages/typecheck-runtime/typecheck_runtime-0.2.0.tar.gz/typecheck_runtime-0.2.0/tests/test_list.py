from __future__ import annotations

from py_typecheck import checked, is_type


def test_list_basic_int():
    assert is_type([1, 2, 3], list[int]) is True
    assert is_type([], list[int]) is True
    assert is_type([1, "x"], list[int]) is False

    assert checked([1, 2, 3], list[int]) == [1, 2, 3]
    assert checked([], list[int]) == []


def test_list_bool_is_not_int():
    assert is_type([True], list[int]) is False
    assert checked([True], list[int]) is None


def test_list_str():
    assert is_type(["a", "b"], list[str]) is True
    assert is_type(["a", 1], list[str]) is False


def test_list_union_elements():
    tp = list[int | str]
    assert is_type([1, "x", 2], tp) is True
    assert is_type([1, True], tp) is False
    assert is_type(["x", object()], tp) is False

    assert checked([1, "x"], tp) == [1, "x"]


def test_nested_lists():
    tp = list[list[int]]
    assert is_type([[1, 2], [3]], tp) is True
    assert is_type([[1, "x"]], tp) is False


def test_list_of_optional():
    tp = list[int | None]
    assert is_type([1, None, 2], tp) is True
    assert is_type([None], tp) is True
    assert is_type([1, "x"], tp) is False


def test_list_wrong_container_type():
    assert is_type((1, 2, 3), list[int]) is False
    assert checked((1, 2, 3), list[int]) is None
