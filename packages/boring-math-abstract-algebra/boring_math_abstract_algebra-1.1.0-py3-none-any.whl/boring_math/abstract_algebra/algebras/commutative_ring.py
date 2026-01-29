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
Commutative Ring
----------------

.. admonition:: Commutative Ring

    Mathematically a Commutative Ring is a Ring whose
    multiplication is commutative.

.. important::

   **Contract:** Ring initializer parameters must have

   - **add** closed, commutative and associative on reps
   - **mult** closed, commutative and associative on reps
   - **one** an identity on reps, ``rep*one == rep == one*rep``
   - **zero** an identity on reps, ``rep+zero == rep == zero+rep``
   - **negate** maps ``rep -> -rep``, ``rep + negate(rep) == zero``
   - **zero** ``!=`` **one**

"""

from collections.abc import Callable, Hashable
from typing import cast
from .ring import Ring, RingElement

__all__ = ['CommutativeRing', 'CommutativeRingElement']


class CommutativeRingElement[H: Hashable](RingElement[H]):
    def __init__(
        self,
        rep: H,
        algebra: 'CommutativeRing[H]',
    ) -> None:
        super().__init__(rep, cast(Ring[H], algebra))

    def __str__(self) -> str:
        """
        :returns: str(self) = CommutativeRingElement<rep>
        """
        return f'CommutativeRingElement<{str(self._rep)}>'


class CommutativeRing[H: Hashable](Ring[H]):
    def __init__(
        self,
        mult: Callable[[H, H], H],
        add: Callable[[H, H], H],
        one: H,
        zero: H,
        negate: Callable[[H], H],
        narrow: Callable[[H], H] | None = None,
    ):
        """
        :param mult: Closed associative function reps.
        :param add: Closed commutative and associative function reps.
        :param one: Representation for multiplicative identity.
        :param zero: Representation for additive identity.
        :param negate: Function mapping element representation to the
                       representation of corresponding negated element.
        :param narrow: Narrow the rep type, many-to-one function. Like
                       choosing an element from a coset of a group.

        """
        super().__init__(
            mult=mult, add=add, one=one, zero=zero, negate=negate, narrow=narrow
        )

    def __call__(self, rep: H) -> CommutativeRingElement[H]:
        """
        Add the unique element to the ring with a with the given,
        perhaps narrowed, ``rep``.

        :param rep: Representation to add if not already present.
        :returns: The unique element with that representation.

        """
        rep = self._narrow(rep)
        return cast(
            CommutativeRingElement[H],
            self._elements.setdefault(
                rep,
                CommutativeRingElement(rep, self),
            ),
        )
