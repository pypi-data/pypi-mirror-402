from __future__ import annotations

from py_typecheck import checked, is_type


def test_tuple_fixed_basic():
    tp = tuple[int, str]
    assert is_type((1, "a"), tp) is True
    assert is_type((1, 2), tp) is False
    assert is_type(("a", 1), tp) is False

    assert checked((1, "a"), tp) == (1, "a")
    assert checked((1, 2), tp) is None


def test_tuple_fixed_length_mismatch():
    tp = tuple[int, str]
    assert is_type((1,), tp) is False
    assert is_type((1, "a", "extra"), tp) is False


def test_tuple_variadic_int():
    tp = tuple[int, ...]
    assert is_type((), tp) is True
    assert is_type((1, 2, 3), tp) is True
    assert is_type((1, "x"), tp) is False

    assert checked((1, 2), tp) == (1, 2)
    assert checked((1, "x"), tp) is None


def test_tuple_union_elements_variadic():
    tp = tuple[int | str, ...]
    assert is_type((1, "x", 2), tp) is True
    assert is_type((True,), tp) is False  # bool != int
    assert is_type(("x", object()), tp) is False


def test_tuple_union_elements_fixed():
    tp = tuple[int | str, bool]
    assert is_type((1, True), tp) is True
    assert is_type(("x", False), tp) is True
    assert is_type((True, True), tp) is False  # první prvek: bool != int

    assert checked((1, True), tp) == (1, True)
    assert checked((True, True), tp) is None


def test_tuple_nested():
    tp = tuple[tuple[int, ...], str]
    assert is_type(((1, 2, 3), "ok"), tp) is True
    assert is_type((("x",), "ok"), tp) is False


def test_tuple_wrong_container_type():
    assert is_type([1, 2], tuple[int, ...]) is False
    assert checked([1, 2], tuple[int, ...]) is None


def test_tuple_unparameterized_matches_any_tuple():
    # get_origin(tuple) -> None a get_args(tuple) -> ()
    # ale get_origin(tuple[...]) -> tuple
    # Tahle větev se trefí pro `tuple[()]`? Ne.
    # Správně: použij `tuple` jako typing object? -> u generik se to liší.
    #
    # Nejstabilnější pro tu větev je použít `tuple` z typing: `tuple[Any, ...]` NE.
    # V našem matcheru se větev `origin is tuple and not args_t` trefí pro `tuple[()]`? ne.
    #
    # Trefí se pro `tuple` vytvořené přes `typing.Tuple` bez parametrů v některých verzích.
    import typing

    tp = typing.Tuple  # noqa: UP006   # legacy typing, no args
    assert is_type((), tp) is True
    assert is_type((1, "x"), tp) is True
    assert is_type([1, 2], tp) is False
