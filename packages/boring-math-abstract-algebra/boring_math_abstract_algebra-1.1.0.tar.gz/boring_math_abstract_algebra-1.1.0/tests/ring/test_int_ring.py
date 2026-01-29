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

from boring_math.abstract_algebra.algebras import Ring

## Ring of integers

# First define a minimal infrastructure

def add(m: int, n: int) -> int:
    return m + n

def mult(m: int, n: int) -> int:
    return m * n

def negate(m: int) -> int:
    return -m

# Define an algebra where consecutive elements don't repeat

rint = Ring[int](
    add = add,
    mult = mult,
    one = 1,
    zero = 0,
    negate = negate,
)


# Test above infrastructure

class TestInt:
    m: int = 4
    n: int = 5
    assert m == 4
    assert n == 5
    assert m is 3 + 1
    assert n is 6 - 1

    # ints pretend to be singletons
    m = 2*(10000 + 21)
    n = 42 + 2*10000
    assert m == 20042
    assert n == 20042
    assert m is not 20000 + 42
    assert n is not 10042 + 10000

class TestRingInt:
    def test_equality_identity(self) -> None:
        zero = rint(0)
        one = rint(1)
        two = rint(2)
        five = rint(5)
        high_five = rint(5)

        assert zero == zero
        assert one == one
        assert five == five
        assert five == high_five
        assert zero != one
        assert one != five
        assert five is high_five

        big1 = rint(40000 + 42)
        big2 = rint(40040 + 2)
        big3 = rint(40040)
        big4 = rint(20020)

        assert big1 == big1
        assert big2 == big2
        assert big3 == big3
        assert big1 == big2
        assert big1 != big3
        assert big1 is big2
        assert big1 is not big3

        assert one + zero is one
        assert one + one is two
        assert (two*big4 + two) is big1
        assert (big4 * two) is big3

    def test_ring_operations(self) -> None:
        neg_one = rint(-1)
        zero = rint(0)
        one = rint(1)
        two = rint(2)
        three = rint(3)
        four = rint(4)
        five = rint(5)
        nine = rint(9)
        ten = rint(10)

        x = five + (three * two + neg_one)
        assert x == ten
        assert x is ten

        ix = five*two - one
        assert ix == nine
        assert ix is nine

        eight = three*four + two*(-two)
        assert eight == two * four
        assert eight is two*(one + one)*two + zero

        assert five*five - five == ten*two

    def test_ring_int_operations(self) -> None:
        zero = rint(0)
        one = rint(1)
        two = rint(2)
        three = rint(3)
        four = rint(4)
        five = rint(5)
        six = rint(6)
        eight = rint(8)
        nine = rint(9)
        ten = rint(10)

        assert 0 * zero is zero
        assert 0 * three is zero
        assert 0 * nine is zero
        assert 42 * zero is zero
        assert 3 * two is six
        assert zero * 0 is zero
        assert ten * 0 is zero
        assert four * 2 is eight
        assert four * 3 is ten + two
        assert four * 1 is four

        assert zero**16 is zero
        assert five**2 is 5*five
        assert five**2 is 5*five
        assert one**42 is one

        assert six**2 - five**2 == three*4 - one
        assert three**2 + (-four)**2 == five**2
