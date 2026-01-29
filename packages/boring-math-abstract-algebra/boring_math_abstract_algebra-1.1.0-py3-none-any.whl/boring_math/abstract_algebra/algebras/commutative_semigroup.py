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
Commutative Semigroup
---------------------

.. admonition:: Commutative Semigroup

    Mathematically a Commutative Semigroup is a set ``S`` along with an
    associative binary operation ``+`` such that

    ``(∀x ∈ S)(∀y ∈ S)(∀z ∈ S) => (x+(y+z)) = ((x+y)+z)``

.. important::

    **Contract:** Group initializer parameters must have

    - **add** closed, commutative and associative on reps

"""

from collections.abc import Callable, Hashable
from typing import Self, cast
from pythonic_fp.fptools.function import compose, partial
from . import BaseSet, BaseElement

__all__ = ['CommutativeSemigroup', 'CommutativeSemigroupElement']


class CommutativeSemigroupElement[H: Hashable](BaseElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'CommutativeSemigroup[H]',
    ) -> None:
        super().__init__(rep, algebra)

    def __str__(self) -> str:
        """
        :returns: str(self) = CommutativeSemigroupElement<rep>

        """
        return f'CommutativeSemigroupElement<{str(self._rep)}>'

    def __add__(self, right: Self) -> Self:
        """
        Add two elements of the same concrete algebra together.

        :param other: Another element within the same algebra.
        :returns: The sum ``self + other``.
        :raises ValueError: If ``self`` and ``other`` are same type but
                            different concrete algebras.
        :raises TypeError: If Addition not defined on the algebra of the elements.
        :raises TypeError: If ``self`` and ``right`` are different types.

        """
        if isinstance(right, type(self)):
            algebra = self._algebra
            if algebra is right._algebra:
                if (add := algebra._add) is not None:
                    return cast(Self, algebra(add(self(), right())))
                else:
                    msg = 'Addition not defined on the algebra of the elements'
                    raise TypeError(msg)
            else:
                msg = 'Addition must be between elements of the same concrete algebra'
                raise ValueError(msg)

        msg = 'Right side of addition wrong type'
        raise TypeError(msg)

    def __radd__(self, left: Self) -> Self:
        """
        When left side of addition does not know how to add right side.

        :param other: Left side of the addition.
        :returns: Never returns, otherwise ``left.__add__(right)``
                  would have worked.
        :raises TypeError: When right side does not know how to
                add the left side to itself.

        """
        msg = 'Left addition operand different type than right'
        raise TypeError(msg)

    def __mul__(self, n: object) -> Self:
        """
        Repeatedly add an element to itself ``n > 0`` times.

        :param n: Object, usually a positive ``int`` or action.
        :returns: If ``n: int`` then self added to itself n times
                  else NotImplemented.
        :raises ValueError: When ``n <= 0``.
        :raises ValueError: If ``self`` and ``other`` are same type but
                            different concrete algebras.
        :raises TypeError: If an add method was not defined on the algebra.
        :raises TypeError: Element multiplication attempted but algebra
                           is not multiplicative.

        """
        algebra = self._algebra
        if isinstance(n, int):
            if n > 0:
                if (add := algebra._add) is None:
                    raise TypeError('Algebra has no addition method')
                r = (r1 := self())
                while n > 1:
                    r, n = add(r1, r), n - 1
                return cast(Self, algebra(r))
            msg = f'For an commutative semigroup n>0, but n={n} was given'
            raise ValueError(msg)
        if isinstance(n, type(self)):
            msg = 'Element multiplication not defined on algebra'
            raise TypeError(msg)
        return NotImplemented

    def __rmul__(self, n: int) -> Self:
        """Repeatedly add an element to itself ``n > 0`` times."""
        return self.__mul__(n)


class CommutativeSemigroup[H: Hashable](BaseSet[H]):
    def __init__(
        self,
        add: Callable[[H, H], H],
        narrow: Callable[[H], H] | None = None,
    ) -> None:
        """
        :param add: Closed commutative and associative function reps.
        :param narrow: Narrow the rep type, many-to-one function. Like
                       choosing an element from a coset of a group.

        """
        super().__init__(narrow=narrow)
        self._add = lambda left, right: compose(partial(add, left), self._narrow)(right)

    def __call__(self, rep: H) -> CommutativeSemigroupElement[H]:
        """
        Add the unique element to the commutative semigroup with the
        given, perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            CommutativeSemigroupElement[H],
            self._elements.setdefault(
                rep,
                CommutativeSemigroupElement(rep, self),
            ),
        )
