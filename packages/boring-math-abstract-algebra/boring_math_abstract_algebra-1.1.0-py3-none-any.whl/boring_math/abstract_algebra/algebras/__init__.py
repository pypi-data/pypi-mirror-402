# Copyright 2025-2026 Geoffrey R. Scheller
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Infrastructure to Represent Abstract Algebras
---------------------------------------------

.. admonition:: Concrete representations of abstract algebras

    Mathematically speaking, an **Algebra** is a **set** with a collection
    of closed n-ary operators

    - Usually 1 or 2 binary operations.
    - Zero, one, or two possibly partial functions for inverses.
    - And nullary functions for designated elements.

    **Element:**

    - Elements know the concrete algebra to which they belong.
    - Each element wraps a hashable immutable representation, called a ``rep``.
    - Binary operations like ``*`` and ``+`` can act on elements, not on
      their representations.

    **Algebra:**

    - Contains a dict of potential elements.
    - Can be used with potentially infinite or continuous algebras.
    - The dict is "quasi-immutable", elements are added in a "natural"
      uniquely deterministic way.
    - Contain user supplied functions and attributes implementing the algebra.
    - Supplied functions take ``rep`` parameters and return ``ref`` values.
    - Supplied attributes are ``rep`` valued.
    - An optional many-to-one function ``narrow: rep -> rep`` to "narrow" the ``rep``
      to a subset of its type.

    The idea is that

    - An element knows the concrete algebra to which it belongs.
    - Each element wraps a hashable representation, called a ``rep``.
    - There is a one-to-one correspondence between ``rep`` values and elements.
    - Algebra operations act on the elements themselves, not on the reps.
    - Algebras know how to manipulate the representations of their elements.

    **Implementation Details**

    - **NaturalMapping** slightly less restrictive version of collections/abc.Mapping.
    - **BaseSet:** Abstract base class for algebras.
    - **BaseElement:** Abstract base class for elements of algebras.

"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Container, Hashable, Iterable, Sized
from types import NotImplementedType
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class NaturalMapping[K: Hashable, V](Sized, Iterable[K], Container[K], Protocol):
    """
    Similar to the collections/abc.Mapping protocol, NaturalMapping
    supports read-only access to dict-like objects which can be extended
    in a "natural" deterministic way.

    """

    def __getitem__(self, key: K) -> V: ...
    def setdefault(self, key: K, default: V) -> V: ...


class BaseElement[H: Hashable](ABC):
    def __init__(
        self,
        rep: H,
        algebra: 'BaseSet[H]',
    ) -> None:
        self._rep = algebra._narrow(rep)
        self._algebra = algebra

    @abstractmethod
    def __str__(self) -> str: ...

    def __call__(self) -> H:
        """
        .. warning::

           A trade off is being made in favor of efficiency over
           encapsulation. An actual reference to the wrapped ``rep``
           is returned to eliminate the overhead of a copy.

        :returns: The narrowed representation wrapped within the element.

        """
        return self._rep

    def __eq__(self, right: object) -> bool:
        """
        Compares if two elements, not necessarily in the same concrete
        algebra, contain equal representations of the same hashable
        type.

        .. warning::

           Any sort of difference in rep narrowing is not taken into
           consideration.

        :param right: Object to be compared with.
        :returns: True if both are elements and the reps compare as equal
                  and are of the same invariant type.

        """
        if not isinstance(right, type(self)):
            return False
        if self is right:
            return True
        if (rep_self := self()) == (rep_right := right()):
            if type(rep_self) is type(rep_right):
                return True
        return False

    def __add__(self, right: Self) -> Self | NotImplementedType:
        return NotImplemented

    def __mul__(self, right: int | Self) -> Self | NotImplementedType:
        return NotImplemented

    def __pow__(self, n: int) -> Self | NotImplementedType:
        return NotImplemented

    def __neg__(self) -> Self:
        msg = 'Negation not defined on the algebra'
        raise TypeError(msg)

    def __sub__(self, right: Self) -> Self | NotImplementedType:
        return NotImplemented

    def __truediv__(self, right: Self) -> Self | NotImplementedType:
        return NotImplemented


class BaseSet[H: Hashable](ABC):
    def __init__(self, narrow: Callable[[H], H] | None = None) -> None:
        self._mult: Callable[[H, H], H] | None = None
        self._one: H | None = None
        self._inv: Callable[[H], H] | None = None
        self._add: Callable[[H, H], H] | None = None
        self._zero: H | None = None
        self._neg: Callable[[H], H] | None = None
        self._elements: NaturalMapping[H, BaseElement[H]] = dict()
        if narrow is None:
            self._narrow: Callable[[H], H] = lambda h: h
        else:
            self._narrow = narrow

    @abstractmethod
    def __call__(self, rep: H) -> BaseElement[H]:
        """
        Add the unique element to the concrete algebra with the given,
        perhaps narrowed, ``rep`` in a uniquely deterministic way.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        ...

    def __eq__(self, right: object) -> bool:
        """
        Compare if two algebras are the same concrete algebra.

        :param right: Object being compared to.
        :returns: True only if ``right`` is the same concrete algebra. False otherwise.

        """
        return self is right

    def narrow_rep_type(self, rep: H) -> H:
        """
        Narrow the type with a concrete algebra's many-to-one
        type "narrowing" function.

        :param rep: Hashable value of type H.
        :returns: The narrowed representation.

        """
        return self._narrow(rep)


# Import concrete implementations after abstract class definitions above
from .semigroup import Semigroup, SemigroupElement  #noqa: E402
from .monoid import Monoid, MonoidElement  #noqa: E402
from .group import Group, GroupElement  # noqa: E402
from .commutative_semigroup import CommutativeSemigroup, CommutativeSemigroupElement  # noqa: E402
from .commutative_monoid import CommutativeMonoid, CommutativeMonoidElement  # noqa: E402
from .abelian_group import AbelianGroup, AbelianGroupElement  # noqa: E402
from .ring import Ring, RingElement  # noqa: E402
from .field import Field, FieldElement  # noqa: E402

__all__ = [
    'Semigroup',
    'SemigroupElement',
    'Monoid',
    'MonoidElement',
    'Group',
    'GroupElement',
    'CommutativeSemigroup',
    'CommutativeSemigroupElement',
    'CommutativeMonoid',
    'CommutativeMonoidElement',
    'AbelianGroup',
    'AbelianGroupElement',
    'Ring',
    'RingElement',
    'Field',
    'FieldElement',
]
