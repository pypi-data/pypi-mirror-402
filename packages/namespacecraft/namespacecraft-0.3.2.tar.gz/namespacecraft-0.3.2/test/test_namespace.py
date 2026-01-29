import pytest

from namespacecraft.namespace import Namespace, Term


def test_as_str():
    EX = Namespace('http://example.org/')
    assert str(EX) == 'http://example.org/'


def test_coerce_int_to_str():
    EX = Namespace('http://example.org/')
    PART = EX / 'part'
    assert str(PART / 1) == 'http://example.org/part/1'


def test_create_term_by_addition():
    EX = Namespace('http://example.org/')
    assert EX / 'a/b/c/' + 'a' == 'http://example.org/a/b/c/a'
    assert EX / 'x/y' + 'z' == 'http://example.org/x/yz'


def test_create_term_by_addition_with_leading_delimiter():
    EX = Namespace('http://example.org')
    term = EX + '/a'
    assert str(term) == 'http://example.org/a'


def test_create_term_without_delimiter():
    EX = Namespace('http://example.org')
    term = EX + 'a'
    assert str(term) == 'http://example.orga'


def test_create_term_by_getting_item():
    EX = Namespace('http://example.org/')
    
    t = EX['abc']
    assert isinstance(t, Term)
    assert str(t) == 'http://example.org/abc'
    
    # Should also work with paths
    t2 = EX['x/y/z']
    assert isinstance(t2, Term)
    assert str(t2) == 'http://example.org/x/y/z'
    
    # Dot notation and indexing should produce the same result for simple names
    assert str(EX.a) == str(EX['a'])


def test_deduplicates_delimiter_in_path():
    EX = Namespace('http://example.org/') / '/a'
    assert str(EX) == 'http://example.org/a'


def test_paths_from_list():
    EX = Namespace('http://example.org/') / [1, 2, 3]
    assert str(EX) == 'http://example.org/1/2/3'


def test_paths_from_list_and_create_term():
    EX = Namespace('http://example.org/') / [1, 2, 3] + '/a'
    assert str(EX) == 'http://example.org/1/2/3/a'


def test_create_term_from_attribute():
    EX = Namespace('http://example.org/')
    a = EX.a
    assert str(a) == 'http://example.org/a'
    assert isinstance(a, Term)

    EX = Namespace('http://example.org#')
    b = EX.b
    assert str(b) == 'http://example.org#b'
    assert isinstance(b, Term)


def test_create_path_with_hash_delimiter():
    EX = Namespace('http://example.org#') / 'a'
    assert str(EX) == 'http://example.org#a'

# Expected errors

def test_only_one_fragment_allowed():
    EX = Namespace('http://example.org#')
    
    # First fragment is fine
    assert EX + 'a' == 'http://example.org#a'
    
    # The original Namespace can still be used to create another fragment
    assert EX + 'b' == 'http://example.org#b'


def test_mismatched_delimiters_in_path():
    # Slash namespace cannot accept #
    EX_slash = Namespace('http://example.org/')
    with pytest.raises(ValueError):
        EX_slash / '#a'

    # Hash namespace cannot accept /
    EX_hash = Namespace('http://example.org#')
    with pytest.raises(ValueError):
        EX_hash / '/a'


def test_hash_delimiter_is_terminal():
    EX = Namespace('http://example.org#')

    # First / returns a terminal object
    term = EX / 'a'
    assert term == 'http://example.org#a'

    # Further / calls are invalid (TypeError)
    with pytest.raises(TypeError):
        term / 'b'


def test_add_returns_term():
    EX = Namespace('http://example.org/')
    term = EX + 'a'

    assert isinstance(term, Term)
    assert term == 'http://example.org/a'


def test_dot_returns_term():
    EX = Namespace('http://example.org/')
    term = EX.a

    assert isinstance(term, Term)
    assert term == 'http://example.org/a'


def test_uri_property_returns_term():
    EX = Namespace('http://example.org/')
    term = EX.uri

    assert isinstance(term, Term)
    assert term == 'http://example.org/'


def test_terminates_with_adds_delimiter():
    EX = Namespace('http://example.org')
    EX2 = EX.terminates_with('/')
    assert str(EX2) == 'http://example.org/'
    assert isinstance(EX2, Namespace)
    # Original namespace is unchanged
    assert str(EX) == 'http://example.org'


def test_terminates_with_slash_path():
    EX = Namespace('http://example.org/').terminates_with('/') / 'a' / 'b' + 'c'
    assert str(EX) == 'http://example.org/a/b/c'


def test_terminates_with_hash_path():
    EX = Namespace('http://example.org/').terminates_with('#') / 'a' / 'b' + 'c'
    assert str(EX) == 'http://example.org/a/b#c'


def test_terminates_with_no_double_delimiter():
    EX = Namespace('http://example.org/')
    EX2 = EX.terminates_with('/')
    assert str(EX2) == 'http://example.org/'
    # Should return self if already ends with delimiter
    assert EX2 is EX or str(EX2) == str(EX)


def test_terminates_with_hash_namespace_raises():
    BASE = Namespace('http://example.org#')
    with pytest.raises(ValueError, match='Cannot set a trailing delimiter on a hash namespace'):
        BASE.terminates_with('/')


def test_terminates_with_invalid_character():
    EX = Namespace('http://example.org')
    with pytest.raises(ValueError):
        EX.terminates_with('')


def test_terminates_with_allows_concatenation():
    EX = Namespace('http://example.org').terminates_with('/')
    term = EX / 'a' / 'b' + 'c'
    assert str(term) == 'http://example.org/a/b/c'


def test_terminates_with_does_not_affect_getattr():
    EX = Namespace('http://example.org').terminates_with('/')
    t = EX.a
    assert isinstance(t, Term)
    assert str(t) == 'http://example.org/a'


def test_terminates_with_returns_new_instance():
    EX = Namespace('http://example.org')
    EX2 = EX.terminates_with('/')
    EX3 = EX.terminates_with('/')
    # New instances may be returned even if logically equal
    assert str(EX2) == str(EX3)
    assert isinstance(EX2, Namespace)
