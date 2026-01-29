from __future__ import annotations

from py_typecheck import checked, is_type


def test_set_basic_int():
    assert is_type({1, 2, 3}, set[int]) is True
    assert is_type(set(), set[int]) is True  # pyright: ignore[]
    assert is_type({1, "x"}, set[int]) is False

    assert checked({1, 2, 3}, set[int]) == {1, 2, 3}
    assert checked(set(), set[int]) == set()  # pyright: ignore[]


def test_set_bool_is_not_int():
    assert is_type({True}, set[int]) is False
    assert checked({True}, set[int]) is None


def test_set_str():
    assert is_type({"a", "b"}, set[str]) is True
    assert is_type({"a", 1}, set[str]) is False


def test_set_union_elements():
    tp = set[int | str]
    assert is_type({1, "x", 2}, tp) is True
    assert is_type({True, 1}, tp) is False  # noqa: B033
    assert is_type({"x", object()}, tp) is False

    assert checked({1, "x"}, tp) == {1, "x"}


def test_set_wrong_container_type():
    assert is_type([1, 2, 3], set[int]) is False
    assert checked([1, 2, 3], set[int]) is None


def test_nested_sets_with_frozenset_elements():
    # set[set[int]] nejde (set není hashable), ale set[frozenset[int]] dává smysl
    tp = set[frozenset[int]]
    assert is_type({frozenset({1, 2}), frozenset({3})}, tp) is True
    assert is_type({frozenset({1, "x"})}, tp) is False


def test_frozenset_wrong_container_type_returns_false():
    tp = frozenset[int]
    assert is_type({1, 2, 3}, tp) is False  # set != frozenset
    assert is_type([1, 2, 3], tp) is False  # list != frozenset
    assert checked({1, 2, 3}, tp) is None


def test_frozenset_wrong_element_type_returns_false():
    tp = frozenset[int]
    assert is_type(frozenset({1, "x"}), tp) is False
    assert checked(frozenset({1, "x"}), tp) is None


def test_frozenset_bool_is_not_int_rule_applies():
    tp = frozenset[int]
    assert is_type(frozenset({True}), tp) is False
    assert checked(frozenset({True}), tp) is None
