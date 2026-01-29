from __future__ import annotations

from py_typecheck import checked, is_type


def test_dict_basic_str_int():
    assert is_type({"a": 1, "b": 2}, dict[str, int]) is True
    assert is_type({}, dict[str, int]) is True

    assert checked({"a": 1}, dict[str, int]) == {"a": 1}
    assert checked({}, dict[str, int]) == {}


def test_dict_wrong_key_type():
    assert is_type({1: 1}, dict[str, int]) is False
    assert checked({1: 1}, dict[str, int]) is None


def test_dict_wrong_value_type():
    assert is_type({"a": "x"}, dict[str, int]) is False
    assert checked({"a": "x"}, dict[str, int]) is None


def test_dict_mixed_wrong_key_and_value():
    assert is_type({1: "x"}, dict[str, int]) is False


def test_dict_union_values():
    tp = dict[str, int | str]
    assert is_type({"a": 1, "b": "x"}, tp) is True
    assert is_type({"a": True}, tp) is False  # bool != int
    assert is_type({"a": object()}, tp) is False

    assert checked({"a": 1, "b": "x"}, tp) == {"a": 1, "b": "x"}


def test_dict_union_keys():
    tp = dict[int | str, int]
    assert is_type({1: 10, "a": 20}, tp) is True
    assert is_type({True: 10}, tp) is False  # bool != int (klíč)
    assert is_type({object(): 1}, tp) is False


def test_nested_dicts():
    tp = dict[str, dict[str, int]]
    assert is_type({"a": {"x": 1}, "b": {}}, tp) is True
    assert is_type({"a": {"x": "nope"}}, tp) is False


def test_dict_wrong_container_type():
    assert is_type([("a", 1)], dict[str, int]) is False
    assert checked([("a", 1)], dict[str, int]) is None


def test_dict_str_to_list_int():
    tp = dict[str, list[int]]
    assert is_type({"a": [1, 2], "b": []}, tp) is True
    assert is_type({"a": [1, True]}, tp) is False
    assert is_type({"a": ["x"]}, tp) is False
