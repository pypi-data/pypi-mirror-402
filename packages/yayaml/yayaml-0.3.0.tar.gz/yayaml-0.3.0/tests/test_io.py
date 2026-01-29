"""Tests the IO module"""

import pytest

from yayaml import (
    RepresenterError,
    add_constructor,
    load_yml,
    write_yml,
    yaml_dumps,
    yaml_dumps_plain,
)

# -----------------------------------------------------------------------------


@pytest.fixture
def example_yaml_files(tmpdir) -> dict:
    paths = dict()

    paths["works"] = tmpdir.join("works.yml")
    with open(paths["works"], "x") as f:
        f.write("---\n{foo: bar, baz: 123, nested: {spam: fish}}\n")

    paths["empty"] = tmpdir.join("empty.yml")
    with open(paths["empty"], "x") as f:
        f.write("---\n")

    paths["fails"] = tmpdir.join("fails.yml")
    with open(paths["fails"], "x") as f:
        f.write("---\nsome, !bad, syntax :: }")

    paths["unicode_characters"] = tmpdir.join("unicode_characters.yml")
    with open(paths["unicode_characters"], "x") as f:
        f.write("---\n{rocket: 🚀}\n")

    return paths


# -----------------------------------------------------------------------------


def test_load_yml(example_yaml_files):
    """Tests _yaml.load_yml function"""
    from ruamel.yaml.parser import ParserError

    paths = example_yaml_files
    expected = dict(foo="bar", baz=123, nested=dict(spam="fish"))

    # Some regular file, returning a dict
    d = load_yml(paths["works"])
    assert d == expected

    # An empty file, returning None
    rv = load_yml(paths["empty"])
    assert rv is None

    # Loads as unicode by default
    rv = load_yml(paths["unicode_characters"])
    assert rv["rocket"] == "🚀"

    # Loading can also fail
    with pytest.raises(ParserError):
        load_yml(paths["fails"])


def test_load_yml_custom_encoding(example_yaml_files, tmpdir):
    """Tests whether it's possible to pass a custom encoding; and use the
    fallback if it does not work."""

    paths = example_yaml_files
    expected = dict(foo="bar", baz=123, nested=dict(spam="fish"))

    d = load_yml(paths["works"], encoding="utf-8")
    assert d == expected

    # with a different encoding, it might still work (depends on file content)
    d = load_yml(paths["works"], encoding="latin-1")
    assert d == expected

    # Indirectly test the fallback to OS-default encoding (utf-8) by checking
    # against unicode characters ...
    d = load_yml(paths["unicode_characters"], encoding="latin-1")
    assert d["rocket"] == "🚀"


def test_load_yml_hints(tmpdir):
    """Tests the YAML error hints"""
    from ruamel.yaml.constructor import ConstructorError
    from ruamel.yaml.parser import ParserError

    class Five:
        pass

    add_constructor("!five", lambda *_: Five())

    # Loading fails, but a hint is shown
    with open(tmpdir.join("fails.yml"), "x") as f:
        f.write("---\n")
        f.write("bar: baz\n")
        f.write("transform:\n")
        f.write("  - [zero, !five, one, two]\n")
        f.write("  - !five\n")
        f.write("spam: fish\n")

    with pytest.raises(ConstructorError, match=r"Hint\(s\) how to resolve"):
        load_yml(tmpdir.join("fails.yml"))

    with pytest.raises(
        ConstructorError, match="could not determine a constructor"
    ):
        load_yml(tmpdir.join("fails.yml"))

    with pytest.raises(ConstructorError, match="details about the error loc"):
        load_yml(tmpdir.join("fails.yml"))

    # Without hints
    with pytest.raises(ConstructorError) as exc_no_hints:
        load_yml(tmpdir.join("fails.yml"), improve_errors=False)
    assert "Hint(s)" not in str(exc_no_hints)

    # Another scenario
    with open(tmpdir.join("fails2.yml"), "x") as f:
        f.write("---\n")
        f.write("bar: baz\n")
        f.write("transform: [foo: !five]\n")

    with pytest.raises(ParserError, match=r"include a space after"):
        load_yml(tmpdir.join("fails2.yml"))


# .............................................................................


def test_write_yml(tmpdir):
    # Test that _something_ is written
    path = tmpdir.join("test.yml")
    write_yml(dict(foo="bar"), path=path)
    assert path.isfile()

    assert load_yml(path) == dict(foo="bar")


# .............................................................................


def test_yaml_dumps_simple():
    """Tests that serialization works for simple objects"""
    dmp = yaml_dumps

    assert dmp(123) == "123\n...\n"
    assert dmp(dict()) == "{}\n"
    assert dmp(dict(foo="bar")) == "{foo: bar}\n"
    assert (
        dmp(dict(foo="bar", spam=[1, 2, 3])) == "foo: bar\nspam: [1, 2, 3]\n"
    )


def test_yaml_dumps():
    """Test the _yaml.yaml_dumps function for string dumps.

    This only tests the functionaltiy provided by the dantro implementation; it
    does not test the behaviour of the ruamel.yaml.dump function itself!
    """
    dumps = yaml_dumps_plain

    # Basics
    assert "foo: bar" in dumps(dict(foo="bar"))

    # Passing additional parameters has an effect
    assert "'foo': 'bar'" in dumps(dict(foo="bar"), default_style="'")
    assert '"foo": "bar"' in dumps(dict(foo="bar"), default_style='"')

    # Custom classes
    class CannotSerializeThis:
        """A class that cannot be serialized"""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class CanSerializeThis(CannotSerializeThis):
        """A class that _can_ be serialized"""

        yaml_tag = "!my_custom_tag"

        @classmethod
        def from_yaml(cls, constructor, node):
            return cls(**constructor.construct_mapping(node.kwargs))

        @classmethod
        def to_yaml(cls, representer, node):
            return representer.represent_mapping(cls.yaml_tag, node.kwargs)

    # Without registering it, it should not work
    with pytest.raises(RepresenterError, match="Could not serialize"):
        dumps(CannotSerializeThis(foo="bar"))

    with pytest.raises(RepresenterError, match="Could not serialize"):
        dumps(CanSerializeThis(foo="bar"))

    # Now, register it
    assert "!my_custom_tag" in dumps(
        CanSerializeThis(foo="bar"), register_classes=(CanSerializeThis,)
    )
