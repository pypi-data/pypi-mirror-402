"""Parametrized tests for YAML constructors.

This module provides granular, parametrized tests for all YAML tags provided
by yayaml, making it easier to identify which specific constructor fails.
"""

import math
import os
import platform

import numpy as np
import pytest

from yayaml import yaml

# -- Built-in function tags ---------------------------------------------------
# These operate on iterables or scalars without unpacking

BUILTIN_TESTS = [
    # any - returns True if any element is truthy
    ("!any", "[false, 0, true]", True, "any_mixed"),
    ("!any", "[false, 0, '']", False, "any_all_falsy"),
    ("!any", "[true, 1, yes]", True, "any_all_truthy"),
    # all - returns True only if all elements are truthy
    ("!all", "[true, 5, 0]", False, "all_with_zero"),
    ("!all", "[true, 1, yes]", True, "all_truthy"),
    ("!all", "[false, 0]", False, "all_falsy"),
    # abs - absolute value
    ("!abs", "-1", 1.0, "abs_negative"),
    ("!abs", "5", 5.0, "abs_positive"),
    ("!abs", "-3.14", 3.14, "abs_float"),
    # int - convert to integer
    ("!int", "1.23", 1, "int_from_float"),
    ("!int", "9.99", 9, "int_truncates"),
    ("!int", "-2.5", -2, "int_negative"),
    # round - round to nearest integer
    ("!round", "9.87", 10, "round_up"),
    ("!round", "9.12", 9, "round_down"),
    ("!round", "9.5", 10, "round_half"),
    # min/max - minimum/maximum of sequence
    ("!min", "[1, 2, 3]", 1, "min_ints"),
    ("!min", "[3, 1, 2]", 1, "min_unsorted"),
    ("!max", "[1, 2, 3]", 3, "max_ints"),
    ("!max", "[3, 1, 2]", 3, "max_unsorted"),
    # sum - sum of sequence
    ("!sum", "[1, 2, 3]", 6, "sum_ints"),
    ("!sum", "[1.5, 2.5]", 4.0, "sum_floats"),
    # prod - product of sequence
    ("!prod", "[2, 3, 4]", 24, "prod_ints"),
    ("!prod", "[2, 3, 0]", 0, "prod_with_zero"),
    # sorted/isorted - sorted lists
    ("!sorted", "[2, 1, 3]", [1, 2, 3], "sorted_ints"),
    ("!sorted", "[3, 1, 2]", [1, 2, 3], "sorted_unsorted"),
    ("!isorted", "[2, 1, 3]", [3, 2, 1], "isorted_ints"),
    ("!isorted", "[1, 3, 2]", [3, 2, 1], "isorted_unsorted"),
    # deepcopy - deep copy of value
    ("!deepcopy", "123", 123, "deepcopy_scalar"),
    ("!deepcopy", "some string", "some string", "deepcopy_string"),
]


@pytest.mark.parametrize("tag,input_val,expected,test_id", BUILTIN_TESTS)
def test_builtin_constructor(tag, input_val, expected, test_id):
    """Test built-in function constructors."""
    result = yaml.load(f"value: {tag} {input_val}")["value"]
    assert result == expected


# -- Operator tags ------------------------------------------------------------
# Binary and unary operators

OPERATOR_TESTS = [
    # Arithmetic operators
    ("!add", "[1, 2]", 3, "add_ints"),
    ("!add", "[1.5, 2.5]", 4.0, "add_floats"),
    ("!sub", "[5, 3]", 2, "sub_ints"),
    ("!sub", "[2, 5]", -3, "sub_negative_result"),
    ("!mul", "[3, 4]", 12, "mul_ints"),
    ("!mul", "[2.5, 4]", 10.0, "mul_float"),
    ("!truediv", "[3, 2]", 1.5, "truediv_ints"),
    ("!truediv", "[10, 4]", 2.5, "truediv_decimal"),
    ("!floordiv", "[3, 2]", 1, "floordiv_ints"),
    ("!floordiv", "[10, 3]", 3, "floordiv_truncates"),
    ("!mod", "[3, 2]", 1, "mod_ints"),
    ("!mod", "[10, 3]", 1, "mod_larger"),
    ("!pow", "[2, 4]", 16, "pow_ints"),
    ("!pow", "[3, 3]", 27, "pow_cubed"),
    ("!pow", "[2, 4, 3]", 1, "pow_mod"),  # pow(2, 4, 3) = 16 % 3 = 1
    # Logical operators
    ("!not", "[true]", False, "not_true"),
    ("!not", "[false]", True, "not_false"),
    ("!and", "[true, false]", False, "and_mixed"),
    ("!and", "[true, true]", True, "and_both_true"),
    ("!or", "[true, false]", True, "or_mixed"),
    ("!or", "[false, false]", False, "or_both_false"),
    ("!xor", "[true, true]", False, "xor_same"),
    ("!xor", "[true, false]", True, "xor_different"),
    # Comparison operators
    ("!lt", "[1, 2]", True, "lt_true"),
    ("!lt", "[2, 1]", False, "lt_false"),
    ("!le", "[2, 2]", True, "le_equal"),
    ("!le", "[3, 2]", False, "le_greater"),
    ("!eq", "[3, 3]", True, "eq_equal"),
    ("!eq", "[3, 4]", False, "eq_not_equal"),
    ("!ne", "[3, 1]", True, "ne_different"),
    ("!ne", "[3, 3]", False, "ne_same"),
    ("!neq", "[3, 1]", True, "neq_different"),  # alias for !ne
    ("!ge", "[2, 2]", True, "ge_equal"),
    ("!ge", "[1, 2]", False, "ge_less"),
    ("!gt", "[4, 3]", True, "gt_true"),
    ("!gt", "[3, 4]", False, "gt_false"),
    # Unary operators
    ("!negate", "[1]", -1, "negate_positive"),
    ("!negate", "[-5]", 5, "negate_negative"),
    ("!invert", "[true]", -2, "invert_true"),  # ~True = -2 in Python
    ("!invert", "[false]", -1, "invert_false"),  # ~False = -1 in Python
    # Container operators
    ("!contains", "[[1, 2, 3], 2]", True, "contains_found"),
    ("!contains", "[[1, 2, 3], 4]", False, "contains_not_found"),
    ("!concat", "[[1, 2], [3, 4]]", [1, 2, 3, 4], "concat_two"),
    ("!concat", "[[1], [2], [3]]", [1, 2, 3], "concat_three"),
]


@pytest.mark.parametrize("tag,input_val,expected,test_id", OPERATOR_TESTS)
def test_operator_constructor(tag, input_val, expected, test_id):
    """Test operator constructors."""
    result = yaml.load(f"value: {tag} {input_val}")["value"]
    assert result == expected


# -- String tags --------------------------------------------------------------

STRING_TESTS = [
    # format - string formatting
    ("!format", '["hello {}!", world]', "hello world!", "format_positional"),
    # join - join strings
    ("!join", '[", ", [a, b, c]]', "a, b, c", "join_comma"),
    ("!join", '["", [a, b, c]]', "abc", "join_empty"),
    # split - split string
    ("!split", '["a b c", " "]', ["a", "b", "c"], "split_space"),
    # oneline/collapse-whitespace - collapse whitespace
    ("!oneline", '"foo  bar  baz"', "foo bar baz", "oneline_spaces"),
    (
        "!collapse-whitespace",
        '"foo  bar  baz"',
        "foo bar baz",
        "collapse_spaces",
    ),
]


@pytest.mark.parametrize("tag,input_val,expected,test_id", STRING_TESTS)
def test_string_constructor(tag, input_val, expected, test_id):
    """Test string manipulation constructors."""
    result = yaml.load(f"value: {tag} {input_val}")["value"]
    assert result == expected


# -- Type tags ----------------------------------------------------------------

TYPE_TESTS = [
    # slice - create slice object
    ("!slice", "5", slice(5), "slice_single"),
    ("!slice", "[5]", slice(5), "slice_list_single"),
    ("!slice", "[0, 10]", slice(0, 10), "slice_start_stop"),
    ("!slice", "[0, 10, 2]", slice(0, 10, 2), "slice_with_step"),
    # range - create range object
    ("!range", "10", range(10), "range_single"),
    ("!range", "[10]", range(10), "range_list_single"),
    ("!range", "[5, 10]", range(5, 10), "range_start_stop"),
    ("!range", "[5, 10, 2]", range(5, 10, 2), "range_with_step"),
]


@pytest.mark.parametrize("tag,input_val,expected,test_id", TYPE_TESTS)
def test_type_constructor(tag, input_val, expected, test_id):
    """Test type constructors."""
    result = yaml.load(f"value: {tag} {input_val}")["value"]
    assert result == expected


# -- Length tag ---------------------------------------------------------------

LENGTH_TESTS = [
    ("!len", "[[1, 2, 3]]", 3, "len_list"),
    ("!len", "[{a: 1, b: 2}]", 2, "len_dict"),
    ("!len", "[[]]", 0, "len_empty_list"),
]


@pytest.mark.parametrize("tag,input_val,expected,test_id", LENGTH_TESTS)
def test_length_constructor(tag, input_val, expected, test_id):
    """Test length constructor with different types."""
    result = yaml.load(f"value: {tag} {input_val}")["value"]
    assert result == expected


# -- NumPy tags ---------------------------------------------------------------

NUMPY_TESTS = [
    # linspace - evenly spaced values
    ("!linspace", "[-1, 1, 5]", [-1.0, -0.5, 0.0, 0.5, 1.0], "linspace_basic"),
    # logspace - logarithmically spaced values
    (
        "!logspace",
        "[1, 4, 4]",
        [10.0, 100.0, 1000.0, 10000.0],
        "logspace_basic",
    ),
]


@pytest.mark.parametrize("tag,input_val,expected,test_id", NUMPY_TESTS)
def test_numpy_constructor(tag, input_val, expected, test_id):
    """Test NumPy-related constructors."""
    result = yaml.load(f"value: {tag} {input_val}")["value"]
    assert result == expected


def test_array_constructor():
    """Test !array constructor creates numpy array."""
    result = yaml.load("value: !array [1, 2, 3]")["value"]
    assert isinstance(result, np.ndarray)
    assert list(result) == [1, 2, 3]


def test_arange_constructor():
    """Test arange separately due to floating point comparison."""
    result = yaml.load("value: !arange [0, 1, 0.2]")["value"]
    expected = [0.0, 0.2, 0.4, 0.6, 0.8]
    assert np.allclose(result, expected)


# -- Conditional tags ---------------------------------------------------------


def test_if_else_constructor():
    """Test if-else conditional constructor."""
    assert yaml.load("value: !if-else [true, yes, no]")["value"] == "yes"
    assert yaml.load("value: !if-else [false, yes, no]")["value"] == "no"


def test_if_unix_else_constructor():
    """Test platform-specific if-unix-else constructor."""
    result = yaml.load("value: !if-unix-else [on_unix, not_unix]")["value"]
    if platform.system() in ("Linux", "Darwin"):
        assert result == "on_unix"
    else:
        assert result == "not_unix"


def test_if_windows_else_constructor():
    """Test platform-specific if-windows-else constructor."""
    result = yaml.load("value: !if-windows-else [on_windows, not_windows]")[
        "value"
    ]
    if platform.system() == "Windows":
        assert result == "on_windows"
    else:
        assert result == "not_windows"


# -- Environment variable tags ------------------------------------------------


def test_getenv_constructor():
    """Test getenv constructor."""
    # Test with known env var
    result = yaml.load("value: !getenv PATH")["value"]
    assert result == os.environ["PATH"]


def test_getenv_with_fallback():
    """Test getenv constructor with fallback."""
    result = yaml.load("value: !getenv [NONEXISTENT_VAR_12345, fallback]")[
        "value"
    ]
    assert result == "fallback"


def test_getboolenv_constructor():
    """Test getboolenv constructor."""
    # Test with fallback values
    result = yaml.load("value: !getboolenv [NONEXISTENT_VAR_12345, 'true']")[
        "value"
    ]
    assert result is True

    result = yaml.load("value: !getboolenv [NONEXISTENT_VAR_12345, '0']")[
        "value"
    ]
    assert result is False


# -- Path tags ----------------------------------------------------------------


def test_expanduser_constructor():
    """Test expanduser constructor."""
    result = yaml.load("value: !expanduser ~/some/path")["value"]
    assert result == os.path.expanduser("~/some/path")


def test_joinpath_constructor():
    """Test joinpath constructor."""
    result = yaml.load("value: !joinpath [foo, bar, baz.txt]")["value"]
    assert result == os.path.join("foo", "bar", "baz.txt")


# -- Listgen tag --------------------------------------------------------------


def test_listgen_from_range():
    """Test listgen constructor with range syntax."""
    result = yaml.load("value: !listgen [0, 10, 2]")["value"]
    assert result == [0, 2, 4, 6, 8]


def test_listgen_with_options():
    """Test listgen constructor with mapping syntax."""
    yaml_str = """
    value: !listgen
      from_range: [0, 10, 3]
      unique: true
      append: [100]
      remove: [0]
      sort: true
    """
    result = yaml.load(yaml_str)["value"]
    assert result == [3, 6, 9, 100]


# -- Expression tag -----------------------------------------------------------


def test_expr_constructor():
    """Test expression constructor."""
    assert yaml.load("value: !expr 1+2*3")["value"] == 7
    assert yaml.load("value: !expr 2**4")["value"] == 16
    assert yaml.load("value: !expr (2+3)*4")["value"] == 20


def test_expr_constructor_special_values():
    """Test expression constructor with special float values."""
    assert yaml.load("value: !expr inf")["value"] == float("inf")
    assert yaml.load("value: !expr -inf")["value"] == float("-inf")
    assert math.isnan(yaml.load("value: !expr NaN")["value"])


# -- Error cases --------------------------------------------------------------

ERROR_TESTS = [
    ("!listgen", "foo", TypeError, "listgen_scalar"),
]


@pytest.mark.parametrize("tag,input_val,exc_type,test_id", ERROR_TESTS)
def test_constructor_error(tag, input_val, exc_type, test_id):
    """Test that constructors raise appropriate errors for invalid input."""
    with pytest.raises(exc_type):
        yaml.load(f"value: {tag} {input_val}")


def test_getboolenv_invalid_value():
    """Test getboolenv raises error for invalid boolean strings."""
    with pytest.raises(ValueError):
        yaml.load("value: !getboolenv [NONEXISTENT_VAR, 'invalid_bool']")


def test_range_too_many_args():
    """Test that !range with too many args raises ConstructorError."""
    import ruamel.yaml.constructor

    with pytest.raises(ruamel.yaml.constructor.ConstructorError):
        yaml.load("value: !range [1, 2, 3, 4]")


# -- Nested constructor tests -------------------------------------------------
# These tests explore how constructors behave with nested/deep construction


def test_len_with_nested_constructors():
    """Test !len with nested constructors to understand deep construction."""
    # Current syntax: wrapper list with inner constructed value
    # !len [[...]] where inner list is the thing to measure

    # Length of a list containing results of other constructors
    result = yaml.load("value: !len [[!add [1, 2], !mul [3, 4]]]")["value"]
    assert result == 2  # list has 2 elements: 3 and 12

    # Length of a constructed list from !sorted
    result = yaml.load("value: !len [!sorted [3, 1, 2]]")["value"]
    assert result == 3


def test_len_with_range_constructor():
    """Test !len measuring a range object."""
    # Length of a range - does deep construction resolve !range first?
    result = yaml.load("value: !len [!range 10]")["value"]
    assert result == 10  # range(10) has 10 elements

    result = yaml.load("value: !len [!range [5, 15]]")["value"]
    assert result == 10  # range(5, 15) has 10 elements


def test_len_with_linspace_constructor():
    """Test !len measuring a linspace result."""
    result = yaml.load("value: !len [!linspace [0, 1, 5]]")["value"]
    assert result == 5  # linspace returns 5 values


def test_nested_arithmetic_constructors():
    """Test deeply nested arithmetic constructors."""
    # Nested arithmetic: (1 + 2) * (3 + 4) = 3 * 7 = 21
    result = yaml.load("value: !mul [!add [1, 2], !add [3, 4]]")["value"]
    assert result == 21

    # Triple nesting: ((1 + 2) * 3) + 4 = 9 + 4 = 13
    result = yaml.load("value: !add [!mul [!add [1, 2], 3], 4]")["value"]
    assert result == 13


def test_conditional_with_nested_comparison():
    """Test !if-else with nested comparison constructors."""
    # if 5 > 3 then "yes" else "no"
    result = yaml.load("value: !if-else [!gt [5, 3], yes, no]")["value"]
    assert result == "yes"

    # if (1+1) == 2 then "math works" else "broken"
    result = yaml.load(
        "value: !if-else [!eq [!add [1, 1], 2], 'math works', broken]"
    )["value"]
    assert result == "math works"
