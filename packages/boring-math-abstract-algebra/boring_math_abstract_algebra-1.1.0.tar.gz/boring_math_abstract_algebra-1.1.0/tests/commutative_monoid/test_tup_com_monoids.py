# Copyright 2025 Geoffrey R. Scheller
#
# Licensed under the Apache License, Version 2.0 (the "License")
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

from typing import Self
from boring_math.abstract_algebra.algebras import CommutativeMonoid

## First define infrastructure

# Define hashable representation type and functions on this type


class Tup53:
    def __init__(self, m: int, n: int):
        rep = (m % 5, n % 3)
        self._rep = rep
        self._hash = hash(rep)

    def __hash__(self) -> int:
        return self._hash

    def __str__(self) -> str:
        return f'Tup53({str(self._rep[0])}, {str(self._rep[1])})'

    def __eq__(self, right: object) -> bool:
        if not isinstance(right, type(self)):
            return NotImplemented
        if self._rep == right._rep:
            return True
        return False

    def __add__(self, right: Self) -> 'Tup53':
        return Tup53(self._rep[0] + right._rep[0], self._rep[1] + right._rep[1])


def add53(left: Tup53, right: Tup53) -> Tup53:
    return left + right


## Test above infrastructure

t00 = Tup53(0, 0)
t01 = Tup53(0, 1)
t02 = Tup53(0, 2)
t10 = Tup53(1, 0)
t11 = Tup53(1, 1)
t12 = Tup53(1, 2)
t20 = Tup53(2, 0)
t21 = Tup53(2, 1)
t22 = Tup53(2, 2)
t30 = Tup53(3, 0)
t31 = Tup53(3, 1)
t32 = Tup53(3, 2)
t40 = Tup53(4, 0)
t41 = Tup53(4, 1)
t42 = Tup53(4, 2)

alg = CommutativeMonoid[Tup53](add=add53, zero=t00)

a00 = alg(t00)
a01 = alg(t01)
a02 = alg(t02)
a10 = alg(t10)
a11 = alg(t11)
a12 = alg(t12)
a20 = alg(t20)
a21 = alg(t21)
a22 = alg(t22)
a30 = alg(t30)
a31 = alg(t31)
a32 = alg(t32)
a40 = alg(t40)
a41 = alg(t41)
a42 = alg(t42)


class TestTup53:
    def test_wrapped_type(self) -> None:
        t0_0 = Tup53(0, 0)
        t22_7 = Tup53(22, 7)
        t7_4 = Tup53(7, 4)
        assert t0_0 == t0_0
        assert t0_0 is t0_0
        assert t22_7 == t7_4
        assert t22_7 is not t7_4

    def test_add(self) -> None:
        assert t00 + t10 == t10
        assert t12 + t00 == t12
        assert t12 + t20 == t32
        assert t42 + t32 == t21
        assert t40 + t41 == t31
        assert t22 + t22 == t41
        assert t30 + t11 == t41
        assert t01 + t02 == t00 == t31 + t22
        assert t01 + t02 is not t31 + t22


class TestComMonoidAlg:
    def test_com_monoid_alg(self) -> None:
        assert a00 == a41 + a12
        assert a00 is a41 + a12
        a0 = a40 + a01 + a30
        a1 = a10 + a11 + a31
        a2 = a20 + a22 + a21
        a3 = a02 + a41 + a32
        a4 = a00 + a12 + a42

        a = a0 + a1 + a2 + a3 + a4
        assert a == a00
        assert a is a00

        assert 42 * a00 == a00 == a00 * 5
        assert 2 * a10 == a20
        assert 4 * a12 == a42
        assert 3 * (a4 + a3) == 3 * a4 + 3 * a3
        assert 5 * (a11 + a12) == 3 * a11 + 2 * (a11 + a12) + 3 * (a00 + a12)
