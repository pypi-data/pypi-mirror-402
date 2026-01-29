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

from boring_math.abstract_algebra.algebras import Field

## Finite field of seven elements


# Restricts int type to just {0, 1, 2, 3, 4, 5, 6}
def narrow(m: int) -> int:
    return m % 7


def add(m: int, n: int) -> int:
    return (m + n) % 7


def mult(m: int, n: int) -> int:
    return (m * n) % 7


def negate(m: int) -> int:
    return (7 - m) % 7 if m > 0 else 0


def invert(m: int) -> int:
    match m % 7:
        case 1:
            return 1
        case 2:
            return 4
        case 3:
            return 5
        case 4:
            return 2
        case 5:
            return 3
        case 6:
            return 6
        case 0:
            raise ValueError('0 is not invertable!')
        case _:
            raise RuntimeError(f'Unexpected value: {(m % 7)!s}')


# Test above infrastructure


class TestFieldMod7:
    def test_equality_identity(self) -> None:
        fmod7 = Field[int](
            add=add,
            mult=mult,
            one=1,
            zero=0,
            negate=negate,
            invert=invert,
            narrow=narrow,
        )

        zero = fmod7(0)
        one = fmod7(1)
        two = fmod7(2)
        three = fmod7(3)
        four = fmod7(4)
        five = fmod7(5)
        six = fmod7(6)

        neg_one = fmod7(-1)
        forty_two = fmod7(42)

        assert zero == zero
        assert one == one
        assert five == five
        assert zero != one
        assert four != three
        assert six == neg_one
        assert forty_two == zero

        assert zero is zero
        assert two is two
        assert five is five
        assert zero is not one
        assert four is not three
        vi = fmod7(6)
        iiiix = fmod7(13)
        assert vi == iiiix
        assert six is vi
        assert vi is iiiix
        assert six is neg_one
        assert forty_two is zero

    def test_field_operations(self) -> None:
        fmod7 = Field[int](
            add=add,
            mult=mult,
            one=1,
            zero=0,
            negate=negate,
            invert=invert,
            narrow=narrow,
        )

        zero = fmod7(0)
        one = fmod7(1)
        two = fmod7(2)
        three = fmod7(3)
        four = fmod7(4)
        five = fmod7(5)
        six = fmod7(6)

        assert zero + zero is zero
        assert five + zero == five
        assert zero + six == six
        assert one + one is two

        assert three * four is five
        assert two * two is four
        assert zero * five is zero
        assert six * one is six
        assert four * two is one
        assert three * five is one

        assert six - two is four
        assert str(five) == 'FieldElement<5>'
        assert str(-five) == 'FieldElement<2>'
        assert -five == two
        assert (-five) is two
        assert -two is five
        assert (-one) * (-one) is one

        assert five / five is  one
        assert two / four is four
        assert six*six is six/six is one
        assert (two + three)*4 is six
 
    def test_field_int_operations(self) -> None:
        fmod7 = Field[int](
            add=add,
            mult=mult,
            one=1,
            zero=0,
            negate=negate,
            invert=invert,
            narrow=narrow,
        )

        zero = fmod7(0)
        one = fmod7(1)
        two = fmod7(2)
        three = fmod7(3)
        four = fmod7(4)
        five = fmod7(5)
        six = fmod7(6)

        assert one * 2 is two
        assert 4 * five is six

        assert three**3 is six
        assert two**5 is four
        assert zero**14 is zero
        assert one**11 is one
        assert six**2 is one
        assert 2*six is five
        assert six*2 is five

        assert six ** (-1) is six
        assert one ** (-1) is one
        assert one ** (-1) is one
        assert two ** (-1) is four
        assert four ** (-1) is two
        assert two ** (-3) is one

        assert one**1 is one
        assert one**0 is one
        assert four**0 is one
        assert two**1 is two
        assert two**2 is four
        assert two**3 is one

        assert one**-3 is one
        assert one**-2 is one
        assert one**-1 is one
        assert six**-1 is six
        assert two**-1 is four
        assert four**-1 is two
        assert three**-1 is five

        try:
            assert zero**-1 is zero
        except ValueError:
            assert True
        else:
            assert False
