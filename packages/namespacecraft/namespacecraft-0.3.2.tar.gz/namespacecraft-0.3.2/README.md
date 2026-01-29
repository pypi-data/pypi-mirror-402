# Namespacecraft

Namespacecraft is a tiny toolkit for composing URI namespaces.

## Use

```pycon
>>> from namespacecraft import Namespace
>>> EX = Namespace('http://example.org/')
>>> EX.a
Term('http://example.org/a')
>>> Namespace('http://example.org').terminates_with('#') / 'a' / 'b' / 'c' + 'x'
Term('http://example.org/a/b/c#x')
```

### Paths

Build paths using the `/` operator.

```pycon
>>> Namespace('http://example.org/') / 'a' / 'b' / 'c'
Namespace('http://example.org/a/b/c')
```

You can pass a list or tuple to `/` to append multiple path components at once.

```pycon
>>> Namespace('http://example.org') / [1, 2, 3]
Namespace('http://example.org/1/2/3')
```

Use `terminates_with()` to set the final delimiter.

```pycon
>>> Namespace('http://example.org').terminates_with('#') / 'a' / 'b'
Namespace('http://example.org/a/b#')
```

### Terms

Create terms by accessing a `Namespace` attribute.

```pycon
>>> EX = Namespace('http://example.org/')
>>> EX.a
Term('http://example.org/a')
```

Or by getting an attribute by name.

```pycon
>>> EX['b']
Term('http://example.org/b')
```

Or with the `+` operator.

```pycon
>>> EX + 1
Term('http://example.org/1')
```

`Namespace` will create terms in any class that initialises from `str`. For example create terms as instances of [`rdflib.URIRef`](https://rdflib.readthedocs.io/en/stable/rdf_terms/?h=uriref#uriref).

```python
from namespacecraft import Namespace
from rdflib import Graph, URIRef


EX = Namespace('http://example.org/', term_cls=URIRef).terminates_with('/') / 'a/b/c'
graph = Graph()
graph.add((EX.s, EX.p, EX.o))
print(graph.serialize(format='turtle'))
```

```turtle
@prefix ns1: <http://example.org/a/b/c/> .

ns1:s ns1:p ns1:o .
```

## Install

```bash
pip install namespacecraft
```

## Gotchas

- The `+` operator returns a `Term` object. Any further `+` operations are just string concatenations.

    ```pycon
    >>> Namespace('http://example.org/') + 'a'
    Term('http://example.org/a')
    >>> Namespace('http://example.org/') + 'a' + 'b'
    Term('http://example.org/ab')
    ```

- Namespaces ending with `#` are always terminal. Any path added via `/` immediately returns a `Term`, and further `/` operations are not allowed.

    ```pycon
    >>> BASE = Namespace('http://example.org#')
    >>> BASE / 'section'
    Term('http://example.org#section')
    >>> (BASE / 'section') / 'subsection'
    TypeError: unsupported operand type(s) for /: 'Term' and 'str'
    ```

- You cannot set a trailing delimiter on a hash namespace. Attempting to do so will raise a `ValueError`.
  
    ```pycon
    >>> BASE = Namespace('http://example.org#')
    >>> BASE.terminates_with('/')
    ValueError: Cannot set a trailing delimiter on a hash namespace
    ```

## Test

```bash
pytest
```
