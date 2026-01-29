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
Abelian Group
-------------

.. admonition:: Abelian Group

    Mathematically an Abelian Group is a Commutative Monoid ``G`` all of
    whose elements have additive inverses.

.. note::

    Addition is used for the group operation.

.. important::

    **Contract:** AbelianGroup initializer parameters must have

    - **add** closed, associative and commutative on reps
    - **zero** additive identity on reps, ``rep.add(zero) == rep == zero.add(rep)``
    - **negate** must me idempotent: ``neg(neg(rep)) == rep``

"""

from collections.abc import Callable, Hashable
from typing import Self, cast
from pythonic_fp.fptools.function import compose
from .commutative_monoid import CommutativeMonoid, CommutativeMonoidElement

__all__ = ['AbelianGroup', 'AbelianGroupElement']


class AbelianGroupElement[H: Hashable](CommutativeMonoidElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'AbelianGroup[H]',
    ) -> None:
        super().__init__(rep, algebra)

    def __str__(self) -> str:
        """
        :returns: str(self) = AbelianGroupElement<rep>

        """
        return f'AbelianGroupElement<{str(self._rep)}>'

    def __mul__(self, n: object) -> Self:
        """
        Repeatedly add an element to itself ``n >= 0`` times.

        :param n: Object, usually an ``int`` or action.
        :returns: If ``n: int`` then self, or its negative, added n times
                  else NotImplemented.
        :raises ValueError: When ``n <= 0``.
        :raises ValueError: If ``self`` and ``other`` are same type but
                            different concrete algebras.
        :raises TypeError: If an add method was not defined on the algebra.
        :raises TypeError: If algebra does not have an additive identity.
        :raises TypeError: Element multiplication attempted but algebra
                           is not multiplicative.

        """
        if isinstance(n, int):
            algebra = self._algebra
            if n >= 0:
                if (add := algebra._add) is None:
                    raise TypeError('Algebra has no addition method')
                if (zero := algebra._zero) is None:
                    raise TypeError('Algebra has no additive identity')
                r, r1 = zero, self()
                while n > 0:
                    r, n = add(r, r1), n - 1
                return cast(Self, algebra(r))
            else:
                g = (g_neg := -self)
                while n < -1:
                    g, n = g + g_neg, n + 1
                return g
        if isinstance(n, type(self)):
            msg = 'Element multiplication not defined on algebra'
            raise TypeError(msg)
        return NotImplemented

    def __rmul__(self, n: int) -> Self:
        return self.__mul__(n)

    def __neg__(self) -> Self:
        """
        Negate the element.

        :returns: The unique additive inverse element to ``self``.
        :raises ValueError: If algebra fails to have additive inverses.

        """
        algebra = self._algebra
        if (negate := algebra._neg) is None:
            raise ValueError('Algebra addition not negatable')
        return cast(Self, algebra(negate(self())))

    def __sub__(self, right: Self) -> Self:
        if not isinstance(right, type(self)):
            msg = 'Subtraction defined only between elements of the algebra'
            raise TypeError(msg)
        return self + (-right)


class AbelianGroup[H: Hashable](CommutativeMonoid[H]):
    def __init__(
        self,
        add: Callable[[H, H], H],
        zero: H,
        negate: Callable[[H], H],
        narrow: Callable[[H], H] | None = None,
    ):
        """
        :param add: Closed, commutative and associative function on reps.
        :param zero: Representation for additive identity.
        :param negate: Function mapping element representation to the
                       representation of corresponding negated element.
        :param narrow: Narrow the rep type, many-to-one function. Like
                       choosing an element from a particular group coset.

        """
        super().__init__(add=add, zero=zero, narrow=narrow)
        self._neg = compose(negate, self._narrow)

    def __call__(self, rep: H) -> AbelianGroupElement[H]:
        """
        Add the unique element to the abelian group with the
        given, perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            AbelianGroupElement[H],
            self._elements.setdefault(
                rep,
                AbelianGroupElement(rep, self),
            ),
        )
