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
Commutative Monoid
------------------

.. admonition:: Commutative Monoid

    Mathematically a commutative Monoid is a Semigroup ``M`` along with
    an identity element ``u``, such that

    ``(∃u ∈ M) => (∀m ∈ M)(u+m = m+u = m)``

    When such an identity element u exists, it is necessarily unique.

.. important::

    **Contract:** Commutative Monoid initializer parameters must have

    - **add** closed commutative and associative on reps
    - **zero** an identity on reps, ``rep+zero == rep == zero+rep``

"""

from collections.abc import Callable, Hashable
from typing import Self, cast
from .commutative_semigroup import CommutativeSemigroup, CommutativeSemigroupElement

__all__ = ['CommutativeMonoid', 'CommutativeMonoidElement']


class CommutativeMonoidElement[H: Hashable](CommutativeSemigroupElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'CommutativeMonoid[H]',
    ) -> None:
        super().__init__(rep, algebra)

    def __str__(self) -> str:
        """
         :returns: str(self) = CommutativeMonoidElement<rep>

        """
        return f'CommutativeMonoidElement<{str(self._rep)}>'

    def __mul__(self, n: object) -> Self:
        """
        Repeatedly add an element to itself ``n >= 0`` times.

        :param n: Object, usually a non-negative ``int`` or action.
        :returns: If ``n: int`` then self added to itself n times
                  else NotImplemented.
        :raises ValueError: When ``n < 0``.
        :raises ValueError: If ``self`` and ``other`` are same type but
                            different concrete algebras.
        :raises TypeError: If algebra fails to have an additive
                           identity element or an addition method.

        """
        if isinstance(n, int):
            algebra = self._algebra
            if n >= 0:
                if (zero := algebra._zero) is None:
                    raise TypeError('Algebra has no additive identity')
                if (add := algebra._add) is None:
                    raise TypeError('Algebra has no add method')
                r, r1 = zero, self()
                while n > 0:
                    r, n = add(r, r1), n - 1
                return cast(Self, algebra(r))
            msg = f'For an commutative monoid n>=0, but n={n} was given'
            raise ValueError(msg)
        if isinstance(n, type(self)):
            msg = 'Element multiplication not defined on algebra'
            raise ValueError(msg)
        return NotImplemented

    def __rmul__(self, n: int) -> Self:
        """Repeatedly add an element to itself ``n > 0`` times."""
        return self.__mul__(n)


class CommutativeMonoid[H: Hashable](CommutativeSemigroup[H]):
    def __init__(
        self,
        add: Callable[[H, H], H],
        zero: H,
        narrow: Callable[[H], H] | None = None,
    ):
        """
        :param add: Closed commutative and associative function reps.
        :param zero: Representation for additive identity.
        :param narrow: Narrow the rep type, many-to-one function. Like
                       choosing an element from a coset of a group.

        """
        super().__init__(add=add, narrow=narrow)
        self._zero = self._narrow(zero)

    def __call__(self, rep: H) -> CommutativeMonoidElement[H]:
        """
        Add the unique element to the commutative monoid with the given,
        perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            CommutativeMonoidElement[H],
            self._elements.setdefault(
                rep,
                CommutativeMonoidElement(rep, self),
            ),
        )
