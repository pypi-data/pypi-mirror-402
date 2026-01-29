"""Tests the yaml constructors"""

import io
import math
import operator
import os
import platform
from typing import Any

import numpy as np
import pytest
import ruamel.yaml
from ruamel.yaml.constructor import ConstructorError

from yayaml import (
    add_constructor,
    raise_improved_exception,
    scalar_node_to_object,
    yaml,
)

# Fixtures --------------------------------------------------------------------


@pytest.fixture()
def yamlstrs() -> dict:
    """Prepares a list of yaml strings to test against"""
    # NOTE Leading indentation is ignored by yaml
    strs = {
        "slice": """
            slices:
             - !slice 5
             - !slice [5]
             - !slice [0, ~]
             - !slice [~, 0]
             - !slice [0, 10, 2]
             - !slice [0, 10, None]
             - !slice [2, None, 2]
        """,
        "range": """
            ranges:
             - !range 10
             - !range [10]
             - !range [5, 10]
             - !range [5, 10, 2]
        """,
        "listgen": """
            lists:
             - !listgen [10]
             - !listgen [0, 10, 2]
             - !listgen
               from_range: [0, 10, 3]
               unique: true
               append: [100]
               remove: [0]
               sort: true
             - !listgen [5, 10, 2]
        """,
        "copy": """
            copy:
              foo: !deepcopy &foo
                bar: baz
              foo2:
                <<: *foo
              seq: !deepcopy
               - 1
               - 2
              scalar: !deepcopy 123
        """,
        "utils": """
            utils:
              # START -- utility-yaml-tags
              any:      !any        [false, 0, true]    # == True
              all:      !all        [true, 5, 0]        # == False

              abs:      !abs        -1          # +1
              int:      !int        1.23        # 1
              round:    !round      9.87        # 10
              sum:      !sum        [1, 2, 3]   # 6
              prod:     !prod       [2, 3, 4]   # 24

              min:      !min        [1, 2, 3]   # 1
              max:      !max        [1, 2, 3]   # 3

              sorted:   !sorted     [2, 1, 3]   # [1, 2, 3]
              isorted:  !isorted    [2, 1, 3]   # [3, 2, 1]

              # Length of an object
              len1:     !len        [[1,2,3]]   # len([1,2,3]) == 3
              len2:     !len        [{foo: 1}]  # len(dict(foo=1)) == 1
              len3:     !len        [foobar]    # len('foobar') == 6

              # Operators
              add:      !add        [1, 2]      # 1 + 2
              sub:      !sub        [2, 1]      # 2 - 1
              mul:      !mul        [3, 4]      # 3 * 4
              mod:      !mod        [3, 2]      # 3 % 2
              pow:      !pow        [2, 4]      # 2 ** 4
              truediv:  !truediv    [3, 2]      # 3 / 2
              floordiv: !floordiv   [3, 2]      # 3 // 2
              pow_mod:  !pow        [2, 4, 3]   # 2 ** 4 % 3

              not:      !not        [true]
              and:      !and        [true, false]
              or:       !or         [true, false]
              xor:      !xor        [true, true]

              lt:       !lt         [1, 2]      # 1 <  2
              le:       !le         [2, 2]      # 2 <= 2
              eq:       !eq         [3, 3]      # 3 == 3
              ne:       !ne         [3, 1]      # 3 != 1
              ge:       !ge         [2, 2]      # 2 >= 2
              gt:       !gt         [4, 3]      # 4 >  3

              negate:   !negate     [1]             # -1
              invert:   !invert     [true]          # ~true
              contains: !contains   [[1,2,3], 4]    # 4 in [1,2,3] == False

              concat:   !concat     [[1,2,3], [4,5], [6,7,8]]  # […]+[…]+[…]+…

              # List generation
              # ... using the paramspace.tools.create_indices function
              list1:    !listgen    [0, 10, 2]   # [0, 2, 4, 6, 8]
              list2:    !listgen
                from_range: [0, 10, 3]
                unique: true
                append: [100]
                remove: [0]
                sort: true

              # ... using np.linspace, np.logspace, np.arange
              lin:      !linspace   [-1, 1, 5]   # [-1., -.5, 0., .5, 1.]
              log:      !logspace   [1, 4, 4]    # [10., 100., 1000., 10000.]
              arange:   !arange     [0, 1, .2]   # [0., .2, .4, .6, .8]

              # String formatting
              format1:  !format     ["{} is not {}", foo, bar]
              format2:  !format
                fstr: "{some_key:}: {some_value:}"
                some_key: fish
                some_value: spam
              format3:  !format
                fstr: "results: {stats[mean]:.2f} ± {stats[std]:.2f}"
                stats:
                  mean: 1.632
                  std:  0.026

              # Collapsing whitespace, e.g. multi-line strings into one-liner.
              # Regardless of YAML syntax, these yield "foo bar baz".
              # The !oneline tag is an alias for !collapse-whitespace
              #
              collapse1: !oneline "foo  bar \n baz "
              collapse2: !oneline >
                foo
                  bar \t
                    baz
              collapse3: !collapse-whitespace |+
                foo
                bar

                baz

              # Conditionals, syntax: (conditional, if true, else)
              conditional_a:      !if-else [true, "a", "not a"]

              # ... can be combined with the operators above.
              eight_is_not_nine:  !if-else [!neq [8, 9], "8≠9", "8==9"]

              # ... platform-specific shortcuts
              on_unix:       !if-unix-else    ["on unix",    "not on unix"]
              on_windows:    !if-windows-else ["on windows", "not on windows"]

              # Joining and splitting strings
              joined_words: !join    # -> "foo | bar | baz"
                - " | "
                - [foo, bar, baz]

              words: !split          # -> [there, are, many, words, in this, sentence]
                - there are many words in this sentence
                - " "
                # - 3                # optional `maxsplit` argument
              # END ---- utility-yaml-tags


              # NOTE Need to choose env. variables that are available in CI
              # START -- envvars-and-path-handling
              # Reading environment variables, optionally with fallback
              PATH:             !getenv PATH   # fails if variable is missing
              username:         !getenv [USER, "unknown_user"]
              home_directory:   !getenv [HOME, "/"]
              run_tests:        !getboolenv [RUN_ALL_MY_TESTS, 'on']  # bool
              run_tests_again:  !getboolenv [RUN_TESTS_AGAIN, '0']    # bool
              run_more_tests:   !getboolenv [RUN_MORE_TESTS, false]   # bool

              # Expanding a path containing `~`
              some_user_path:   !expanduser ~/some/path

              # Joining paths
              some_joined_path: !joinpath      # -> "~/foo/bar/../spam.txt"
                - "~"
                - foo
                - bar
                - ..
                - spam.txt
              # END ---- envvars-and-path-handling

              # More tests that don't need to be part of the docs
              pow_mod2: !pow {x: 2, y: 4, z: 3}
        """,
        #
        # Failing or warning cases
        ("_listgen_scalar", TypeError): "string_node: !listgen foo",
        ("_bad_str2bool", ValueError): "foo: !getboolenv [FOO, bad value]",
    }

    return strs


# -- Tests --------------------------------------------------------------------
# .. Legacy tests (not easy to extend) ........................................
# TODO Rewrite these


def test_load_and_safe(yamlstrs):
    """Tests whether the constructor and representers work"""
    # Test plain loading
    for name, ystr in yamlstrs.items():
        print("\n\nName of yamlstr that will be loaded: ", name)

        if isinstance(name, tuple):
            # Expected to warn or raise
            if len(name) == 2:
                name, exc = name
                warn = None
            elif len(name) == 3:
                name, exc, warn = name

            # Distinguish three cases
            if warn and exc:
                with pytest.raises(exc):
                    with pytest.warns(warn):
                        yaml.load(ystr)

            elif warn and not exc:
                with pytest.warns(warn):
                    yaml.load(ystr)

            elif exc and not warn:
                with pytest.raises(exc):
                    yaml.load(ystr)

            continue

        # else: Expected to load correctly
        obj = yaml.load(ystr)

        # Test the representer runs through
        stream = io.StringIO("")
        yaml.dump(obj, stream=stream)
        output = "\n".join(stream.readlines())

        # TODO Test output


def test_correctness(yamlstrs):
    """Tests the correctness of the constructors"""
    res = {}

    # Load the resolved yaml strings
    for name, ystr in yamlstrs.items():
        print("Name of yamlstr that will be loaded: ", name)
        if isinstance(name, tuple):
            # Will fail, don't use
            continue
        res[name] = yaml.load(ystr)

    # Test the utility constructors
    utils = res["utils"]["utils"]
    assert utils["any"] == any([False, 0, True])
    assert utils["all"] == all([True, 5, 0])
    assert utils["abs"] == abs(-1)
    assert utils["int"] == int(1.23)
    assert utils["round"] == round(9.87) == 10
    assert utils["min"] == min([1, 2, 3])
    assert utils["max"] == max([1, 2, 3])
    assert utils["sorted"] == sorted([2, 1, 3])
    assert utils["isorted"] == sorted([2, 1, 3], reverse=True)
    assert utils["sum"] == sum([1, 2, 3])
    assert utils["prod"] == 2 * 3 * 4
    assert utils["len1"] == 3
    assert utils["len2"] == 1
    assert utils["len3"] == len("foobar")
    assert utils["add"] == operator.add(*[1, 2])
    assert utils["sub"] == operator.sub(*[2, 1])
    assert utils["mul"] == operator.mul(*[3, 4])
    assert utils["truediv"] == operator.truediv(*[3, 2])
    assert utils["floordiv"] == operator.floordiv(*[3, 2])
    assert utils["mod"] == operator.mod(*[3, 2])
    assert utils["pow"] == 2**4
    assert utils["pow_mod"] == 2**4 % 3 == pow(2, 4, 3)
    assert utils["pow_mod2"] == 2**4 % 3 == pow(2, 4, 3)
    assert utils["not"] == operator.not_(*[True])
    assert utils["and"] == operator.and_(*[True, False])
    assert utils["or"] == operator.or_(*[True, False])
    assert utils["xor"] == operator.xor(*[True, True])
    assert utils["lt"] == operator.lt(*[1, 2])
    assert utils["le"] == operator.le(*[2, 2])
    assert utils["eq"] == operator.eq(*[3, 3])
    assert utils["ne"] == operator.ne(*[3, 1])
    assert utils["ge"] == operator.ge(*[2, 2])
    assert utils["gt"] == operator.gt(*[4, 3])
    assert utils["negate"] == operator.neg(*[1])
    assert utils["invert"] == operator.invert(*[True])
    assert utils["contains"] == operator.contains(*[[1, 2, 3], 4])
    assert utils["concat"] == [1, 2, 3] + [4, 5] + [6, 7, 8]
    assert utils["format1"] == "foo is not bar"
    assert utils["format2"] == "fish: spam"
    assert utils["format3"] == "results: 1.63 ± 0.03"
    assert utils["collapse1"] == "foo bar baz"
    assert utils["collapse2"] == "foo bar baz"
    assert utils["collapse3"] == "foo bar baz"
    assert utils["joined_words"] == "foo | bar | baz"
    assert utils["words"] == [
        "there",
        "are",
        "many",
        "words",
        "in",
        "this",
        "sentence",
    ]

    assert utils["list1"] == [0, 2, 4, 6, 8]
    assert utils["list2"] == [3, 6, 9, 100]
    assert utils["lin"] == [-1.0, -0.5, 0.0, 0.5, 1.0]
    assert utils["log"] == [10.0, 100.0, 1000.0, 10000.0]
    assert np.isclose(utils["arange"], [0.0, 0.2, 0.4, 0.6, 0.8]).all()

    assert utils["some_user_path"] == os.path.expanduser("~/some/path")

    assert utils["PATH"] == os.environ["PATH"]
    assert utils["username"] == os.environ.get("USER", "unknown_user")
    assert utils["home_directory"] == os.environ.get("HOME", "/")

    assert utils["run_tests"] is True
    assert utils["run_tests_again"] is False
    assert utils["run_more_tests"] is False

    assert utils["conditional_a"] == "a"
    assert utils["eight_is_not_nine"] == "8≠9"

    assert (
        utils["on_unix"] == "on_unix"
        if platform.system() not in ("Darwin", "Linux")
        else "not on unix"
    )
    assert (
        utils["on_windows"] == "on_windows"
        if platform.system() == "Windows"
        else "not on windows"
    )


# -- Newer tests --------------------------------------------------------------
# .. Representation ...........................................................


def test_represent_custom_class():
    from collections import namedtuple

    from yayaml import add_representer, build_representer, yaml_dumps

    Point = namedtuple("Point", ["x", "y"])
    pt = Point(123, 234)

    # FIXME This somehow breaks yaml_dumps
    # with pytest.raises(RepresenterError, match="Could not serialize"):
    #     yaml_dumps(pt)

    # Register the representer
    add_representer(
        Point,
        build_representer(lambda pt: dict(x=pt.x, y=pt.y)),
    )

    # This should work now
    assert "123" in yaml_dumps(dict(pt=pt))

    # How about some type that can be represented as a scalar
    MyInt = namedtuple("MyInt", ["value"])
    my_int = MyInt(123)

    # FIXME This somehow breaks yaml_dumps
    # with pytest.raises(RepresenterError, match="Could not serialize"):
    #     yaml_dumps(my_int)

    add_representer(
        MyInt,
        build_representer(lambda my_int: my_int.value),
        _yaml=yaml,
    )

    assert "123" in yaml_dumps(my_int)


def test_representer_decorator():
    from collections import namedtuple

    from yayaml import build_representer, is_representer, yaml_dumps

    Point = namedtuple("Point", ["x", "y"])

    @is_representer(Point, _yaml=yaml)
    def represent_point(r, pt, *, tag: str):
        return r.represent_sequence(tag, [pt.x, pt.y])

    pt = Point(123, 234)
    dump = yaml_dumps(dict(pt=pt))
    assert "123" in dump
    assert "!Point [123, 234]" in dump

    # Custom tag
    @is_representer(Point, tag="!my_point")
    def represent_point_again(r, pt, *, tag: str):
        return r.represent_sequence(tag, [pt.x, pt.y])

    dump = yaml_dumps(dict(pt=pt), _yaml=yaml)
    assert "123" in dump
    assert "!my_point [123, 234]" in dump


# .. Construction .............................................................


def test_construction_error_messages():
    # For function-based constructors, information is added
    with pytest.raises(
        ruamel.yaml.constructor.ConstructorError, match="expected at most 3"
    ):
        yaml.load("!range [1,2,3,4]")


def test_scalar_node_construction():
    assert yaml.load("!deepcopy 1") == 1
    assert yaml.load("!deepcopy 1.2") == 1.2
    assert yaml.load("!deepcopy inf") == float("inf")
    assert yaml.load("!deepcopy some string") == "some string"

    assert yaml.load("!deepcopy false") is False
    assert yaml.load("!deepcopy no") is False

    assert yaml.load("!deepcopy ~") is None
    assert yaml.load("!deepcopy null") is None


def test_scalar_node_to_object():
    """Test the scalar_node_to_object helper function

    NOTE It is important here to not only test with a tagged node, but also
         with untagged nodes.
    """

    def to_node(d: Any, *, tag=None, set_tag: bool = True):
        """Given some data, represents it as a node and allows to remove the
        tag information.
        """
        node = yaml.representer.represent_data(d)
        if set_tag:
            node.tag = tag
        return node

    loader = yaml.constructor
    to_obj = scalar_node_to_object

    to_test = (
        # Null
        (None, None),
        ("~", None),
        ("null", None),
        # Boolean
        (True, True),
        ("true", True),
        ("TrUe", True),
        ("y", True),
        ("yEs", True),
        ("oN", True),
        (False, False),
        ("false", False),
        ("FaLsE", False),
        ("n", False),
        ("nO", False),
        ("oFf", False),
        # Int
        (123, 123),
        ("0", 0),
        ("1", 1),
        ("-123", -123),
        ("+123", 123),
        # Float
        # (1.23, 1.23),  # FIXME ... some upstream error here!
        ("1.23", 1.23),
        ("-2.34", -2.34),
        ("1e10", 1e10),
        ("1.23e-10", 1.23e-10),
        (".inf", float("inf")),
        ("-.inf", -float("inf")),
        (".NaN", float("nan")),
        (".nan", float("nan")),
        ("nan", float("nan")),
        # String
        ("", ""),  # not null!
        ("some string", "some string"),
        ("123.45.67", "123.45.67"),
        # Exceptions
        ([1, 2, 3], ConstructorError),
        (dict(foo="bar"), ConstructorError),
    )

    for s, expected in to_test:
        print(f"Case: ({repr(s)}, {repr(expected)})")
        node_tagged = to_node(s, set_tag=False)
        node_untagged = to_node(s)
        print(f"\t{node_tagged}")

        if isinstance(expected, type) and issubclass(expected, Exception):
            print(f"\t… should raise {expected}")

            with pytest.raises(expected):
                to_obj(loader, node_tagged)
            with pytest.raises(expected):
                to_obj(loader, node_untagged)

        else:
            print(
                f"\t… should be converted to:  "
                f"{type(expected).__name__} {repr(expected)} ..."
            )

            actual_tagged = to_obj(loader, node_tagged)
            actual_untagged = to_obj(loader, node_untagged)

            # Check type and value
            assert type(actual_tagged) is type(expected)
            assert type(actual_untagged) is type(expected)

            if isinstance(expected, float) and math.isnan(expected):
                assert math.isnan(actual_tagged)
                assert math.isnan(actual_untagged)
            else:
                assert actual_tagged == expected
                assert actual_untagged == expected


def test_expr_constructor():
    """Tests the expression constructor"""
    tstr = """
        one:   !expr 1*2*3
        two:   !expr 9 / 2
        three: !expr 2**4
        four:  !expr 1e-10
        five:  !expr 1E10
        six:   !expr inf
        seven: !expr NaN
        eight: !expr (2 + 3) * 4
        nine:  !expr -inf
    """

    # Load the string using the tools module, where the constructor was added
    d = yaml.load(tstr)

    # Assert correctness
    assert d["one"] == 1 * 2 * 3
    assert d["two"] == 9 / 2
    assert d["three"] == 2**4
    assert d["four"] == eval("1e-10") == 10.0 ** (-10)
    assert d["five"] == eval("1E10") == 10.0**10
    assert d["six"] == np.inf
    assert np.isnan(d["seven"])
    assert d["eight"] == (2 + 3) * 4


# .. Error messages ...........................................................


def test_construction_error_hint_registration():
    add_constructor(
        "!foo", lambda l, n: "some foo constant", hint="some hint", _yaml=yaml
    )
    from yayaml.exceptions import YAML_ERROR_HINTS

    assert YAML_ERROR_HINTS[-2][1] == "some hint"

    add_constructor("!bar", lambda l, n: "baz", hint=(True, "another hint"))
    from yayaml.exceptions import YAML_ERROR_HINTS

    assert YAML_ERROR_HINTS[-2][1] == "another hint"


def test_raise_improved_exception():
    """Tests dantro.exceptions.raise_improve_exception"""

    # Need a function to test this more easily
    def test_improved_raise(
        ExcType: type = Exception,
        msg: str = "no error message",
        ExceptType: type = Exception,
        **kwargs,
    ):
        try:
            raise ExcType(msg)
        except ExceptType as exc:
            raise_improved_exception(exc, **kwargs)

    # Here we go ...
    with pytest.raises(Exception, match="no error message"):
        test_improved_raise()

    # Without active exception to re-raise
    with pytest.raises(Exception, match="No active exception"):
        raise_improved_exception(Exception(""))

    # Now with hints
    with pytest.raises(Exception, match="some hint"):
        test_improved_raise(hints=[(lambda _: True, "some hint")])
