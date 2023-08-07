"""Numpydoclint introspection.

Numpydoclint introspection is fully static and based solely on the [ast](https://docs.python.org/3/library/ast.html) and
[tokenize](https://docs.python.org/3/library/tokenize.html) Python built-in libraries. Introspection consists of three main parts:

- Introspection: searching for objects.
- Filtering: smart filtering of found objects and propagation of ignored errors.
- Object infos: storing information about the objects found and their metadata.
"""
from numpydoclint.introspection.introspectors import Introspector
from numpydoclint.introspection.object_infos import ObjectInfo

__all__ = ["Introspector", "ObjectInfo"]
