import pytest
from namespacecraft import Namespace, Term


def test_term_is_str_subclass():
    term = Term('http://example.org/a')
    assert isinstance(term, str)
    assert isinstance(term, Term)


def test_term_is_not_namespace():
    term = Term('http://example.org/a')
    assert not isinstance(term, Namespace)


def test_term_repr():
    term = Term('http://example.org/a')
    assert repr(term) == "Term('http://example.org/a')"


def test_term_is_terminal_no_path_extension():
    term = Term('http://example.org/a')

    with pytest.raises(TypeError):
        term / 'b'


def test_term_has_no_attribute_namespace_semantics():
    term = Term('http://example.org/a')

    # Attribute access should behave like str, not Namespace
    with pytest.raises(AttributeError):
        _ = term.b
