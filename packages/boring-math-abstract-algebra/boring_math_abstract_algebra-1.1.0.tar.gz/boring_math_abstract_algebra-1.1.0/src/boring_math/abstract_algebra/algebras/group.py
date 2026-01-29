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
Group
-----

.. admonition:: Group

    Mathematically a Group is a Monoid ``G`` all of whose elements
    have multiplicative inverses.

.. caution::

   No assumptions are made whether or not the group is Abelian.

.. important::

   **Contract:** Group initializer parameters must have

   - **mult** closed and associative on reps
   - **one** an identity on reps, ``rep*one == rep == one*rep``
   - **inv** must me idempotent: ``inv(inv(rep)) == rep``

"""

from collections.abc import Callable, Hashable
from typing import Self, cast
from pythonic_fp.fptools.function import compose
from .monoid import Monoid, MonoidElement

__all__ = ['Group', 'GroupElement']


class GroupElement[H: Hashable](MonoidElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'Group[H]',
    ) -> None:
        super().__init__(rep, algebra)

    def __str__(self) -> str:
        """
        :returns: str(self) = GroupElement<rep>

        """
        return f'GroupElement<{str(self._rep)}>'

    def __pow__(self, n: int) -> Self:
        """
        Raise the element to the power of ``n``.

        :param n: The ``int`` power to raise the element to.
        :returns: The element (or its inverse) raised to the integer``n`` power.
        :raises ValueError: If element's algebra 
        :raises ValueError: If ``self`` and ``other`` are same type but different concrete groups.
        :raises ValueError: If algebra fails to have an identity or elements not invertible.

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
            g = (g_inv := type(self)(invert(self()), cast(Group[H], algebra)))
            while n < -1:
                g, n = g * g_inv, n + 1
            return g


class Group[H: Hashable](Monoid[H]):
    def __init__(
        self,
        mult: Callable[[H, H], H],
        one: H,
        invert: Callable[[H], H],
        narrow: Callable[[H], H] | None = None,
    ):
        """
        :param mult: Associative function ``H X H -> H`` on representations.
        :param one: Representation for multiplicative identity.
        :param invert: Function ``H -> H`` mapping element representation to
                       the representation of corresponding inverse element.
        :param narrow: Narrow the rep type, many-to-one function. Like
                       choosing an element from a coset of a group.

        """
        super().__init__(mult=mult, one=one, narrow=narrow)
        self._inv = compose(invert, self._narrow)

    def __call__(self, rep: H) -> GroupElement[H]:
        """
        Add the unique element to the group with a with the given,
        perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            GroupElement[H],
            self._elements.setdefault(
                rep,
                GroupElement(rep, self),
            ),
        )
