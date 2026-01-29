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
Orderings on Algebras
---------------------

.. admonition:: Protocols for orderings of algebraic structures.

    Total and partial orderings on algebras.

"""

from typing import Protocol, Self

__all__ = ['PartialOrder', 'TotalOrder']


class PartialOrder[O](Protocol):
    """Partially Ordered.

    .. important::

        Contract: Operator ``<=`` is reflexive, anti-symmetric and transitive.

    """

    def __le__(self, right: Self) -> bool:
        """
        :param right: RHS of ``<=`` comparison
        :returns: ``self <= right``

        """
        ...


class TotalOrder[O](PartialOrder[O], Protocol):
    """Totally Ordered.

    .. important::

        Contract: Overloaded methods must still define a total order.

    """

    def __lt__(self, right: Self) -> bool:
        """
        :param right: RHS of ``<`` comparison
        :returns: ``self < right``

        """
        return self <= right and self != right

    def __ge__(self, right: Self) -> bool:
        """
        :param right: RHS of ``>=`` comparison
        :returns: ``self >= right``

        """
        return not self < right

    def __gt__(self, right: Self) -> bool:
        """
        :param right: RHS of ``>`` comparison
        :returns: ``self > right``

        """
        return not self <= right
