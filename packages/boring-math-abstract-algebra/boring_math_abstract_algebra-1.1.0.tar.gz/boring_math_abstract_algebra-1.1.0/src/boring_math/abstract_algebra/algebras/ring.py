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
Ring
----

.. admonition:: Ring

    Mathematically a Ring is an abelian group under addition and a
    Monoid under multiplication. The additive and multiplicative
    identities are denoted ``one`` and ``zero`` respectfully.

    By convention ``one != zero``, otherwise the algebra consists
    of just one unique element.

.. important::

   **Contract:** Ring initializer parameters must have

   - **add** closed, commutative and associative on reps
   - **mult** closed and associative on reps
   - **one** an identity on reps, ``rep*one == rep == one*rep``
   - **zero** an identity on reps, ``rep+zero == rep == zero+rep``
   - **negate** maps ``rep -> -rep``, ``rep + negate(rep) == zero``
   - **zero** ``!=`` **one**

"""

from collections.abc import Callable, Hashable
from typing import Self, cast
from pythonic_fp.fptools.function import compose, partial
from .abelian_group import AbelianGroup, AbelianGroupElement

__all__ = ['Ring', 'RingElement']


class RingElement[H: Hashable](AbelianGroupElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'Ring[H]',
    ) -> None:
        super().__init__(rep, cast(AbelianGroup[H], algebra))

    def __str__(self) -> str:
        """
        :returns: str(self) = RingElement<rep>

        """
        return f'RingElement<{str(self._rep)}>'

    def __mul__(self, right: object) -> Self:
        """
        Left multiplication for ``*`` operator.

        :param right: Object ``left`` should be an element of same
                      concrete algebra or an ``int``.
        :returns: Algebra product, the sum of the element ``right`` times,
                  or ``NotImplemented``.
        :raises ValueError: If either right not an element of the same
                            concrete algebra  or ``right: int < 0``.
        :raises TypeError: Multiplication nor defined on the algebra
                           that ``self`` is a member of.

        """
        if isinstance(right, int):
            return super().__mul__(right)

        if isinstance(right, type(self)):
            algebra = self._algebra
            if algebra is right._algebra:
                if (mult := algebra._mult) is not None:
                    return cast(Self, algebra(mult(self(), right())))
                else:
                    msg = 'Multiplication not defined on the algebra'
                    raise TypeError(msg)
            else:
                msg = 'Multiplication must be between elements of the same concrete algebra'
                raise ValueError(msg)

        return NotImplemented

    def __rmul__(self, left: object) -> Self:
        """
        Right multiplication for ``*`` operator.

        :param left: Object ``left`` should be an ``int``.
        :returns: The sum of the element ``left`` times.
        :raises TypeError: If object on left does not act
                           on object on right

        """
        if isinstance(left, int):
            return self.__mul__(left)

        msg = 'Object on left does not act on object on right.'
        raise TypeError(msg)

    def __pow__(self, n: int) -> Self:
        """
        Raise element to power to the ``int`` power of ``n>=0``.

        :param n: The ``int`` power to raise the element to.
        :returns: The element  raised to the non-negative integer
                  ``n`` power.
        :raises ValueError: If algebra is not multiplicative.
        :raises ValueError: If algebra does not have a multiplicative
                            identity element.
        :raises ValueError: If ``n < 0``.

        """
        algebra = self._algebra
        if (mult := algebra._mult) is None:
            raise ValueError('Algebra has no multiplication method')
        if (one := algebra._one) is None:
            raise ValueError('Algebra has no multiplicative identity')
        if n >= 0:
            r, r1 = one, self()
            while n > 0:
                r, n = mult(r, r1), n - 1
            return cast(Self, algebra(r))

        msg = f'For a Ring n>=0, but n={n} was given'
        raise ValueError(msg)


class Ring[H: Hashable](AbelianGroup[H]):
    def __init__(
        self,
        add: Callable[[H, H], H],
        mult: Callable[[H, H], H],
        one: H,
        zero: H,
        negate: Callable[[H], H],
        narrow: Callable[[H], H] | None = None,
    ):
        """
        :param add: Closed commutative and associative function reps.
        :param mult: Closed associative function reps.
        :param one: Representation for multiplicative identity.
        :param zero: Representation for additive identity.
        :param negate: Function mapping element representation to the
                       representation of corresponding negated element.
        :param narrow: Narrow the rep type, many-to-one function. Like
                       choosing an element from a coset of a group.

        """
        super().__init__(add=add, zero=zero, negate=negate, narrow=narrow)
        self._one = self._narrow(one)
        self._mult = lambda left, right: compose(partial(mult, left), self._narrow)(right)

    def __call__(self, rep: H) -> RingElement[H]:
        """
        Add the unique element to the ring with a with the given,
        perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            RingElement[H],
            self._elements.setdefault(
                rep,
                RingElement(rep, self),
            ),
        )
