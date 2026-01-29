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
Field
-----

.. admonition:: Field

    Mathematically a Field is a Commutative Ring all whose non-zero
    elements have multiplicative inverses.

    By convention ``one != zero``, otherwise the algebra consists
    of just one unique element.

.. important::

    **Contract:** Field initializer parameters must have

    - **add** closed, commutative and associative on reps
    - **mult** closed, commutative and associative on reps
    - **one** an identity on reps, ``rep*one == rep == one*rep``
    - **zero** an identity on reps, ``rep+zero == rep == zero+rep``
    - **inv** is the mult inverse function on all non-zero reps
    - **negate** function to negate all proper rep values
    - **invert** function to invert all proper rep values
    - **zero** ``!=`` **one** (by convention)

"""

from collections.abc import Callable, Hashable
from typing import Self, cast
from pythonic_fp.fptools.function import compose
from .commutative_ring import CommutativeRing, CommutativeRingElement

__all__ = ['Field', 'FieldElement']


class FieldElement[H: Hashable](CommutativeRingElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'Field[H]',
    ) -> None:
        super().__init__(rep, cast(CommutativeRing[H], algebra))

    def __str__(self) -> str:
        """
        :returns: str(self) = FieldElement<rep>

        """
        return f'FieldElement<{str(self._rep)}>'

    def __pow__(self, n: int) -> Self:
        """
        Raise the element to the ``int`` power of ``n``.

        :param n: The ``int`` power to raise the element to.
        :returns: The element (or its inverse) raised to an ``int`` power.
        :raises ValueError: If algebra is not multiplicative.
        :raises ValueError: If algebra does not have a multiplicative identity element.
        :raises ValueError: If algebra does not have multiplicative inverses.

        """
        algebra = self._algebra
        if (mult := algebra._mult) is None:
            raise ValueError('Algebra has no multiplication method')
        if (one := algebra._one) is None:
            raise ValueError('Algebra has no multiplicative identity')
        if (invert := algebra._inv) is None:
            raise ValueError('Algebra not invertable')
        if n >= 0:
            r, r1 = one, self()
            while n > 0:
                r, n = mult(r, r1), n - 1
            return cast(Self, algebra(r))
        else:
            r_inv = invert(self())
            r, r1 = r_inv, r_inv
            while n < -1:
                r, n = mult(r, r1), n + 1
            return cast(Self, algebra(r))

    def __truediv__(self, right: Self) -> Self:
        """Divide self by right."""
        return self * right**(-1)


class Field[H: Hashable](CommutativeRing[H]):
    def __init__(
        self,
        mult: Callable[[H, H], H],
        add: Callable[[H, H], H],
        one: H,
        zero: H,
        negate: Callable[[H], H],
        invert: Callable[[H], H],
        narrow: Callable[[H], H] | None = None,
    ):
        """
        :param mult: Closed associative function reps.
        :param add: Closed commutative and associative function reps.
        :param one: Representation for multiplicative identity.
        :param zero: Representation for additive identity.
        :param negate: Function mapping element representation to the
                       representation of corresponding negated element.
        :param invert: Function mapping non-zero element representations
                       to their multiplicative inverses.
        :param narrow: Narrow the rep type, many to one function, like
                       choosing an element from a coset of a group,

        """
        super().__init__(
            mult=mult,
            add=add,
            one=one,
            zero=zero,
            negate=negate,
            narrow=narrow,
        )
        self._inv = compose(invert, self._narrow)

    def __call__(self, rep: H) -> FieldElement[H]:
        """
        Add the unique element to the field with a with the given,
        perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            FieldElement[H],
            self._elements.setdefault(
                rep,
                FieldElement(rep, self),
            ),
        )
