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

import re
from typing import Self
from boring_math.abstract_algebra.algebras import Monoid

## First define infrastructure

# Define hashable representation type and functions on this type


class AB:
    def __init__(self, ab: str):
        pat = re.compile('[ab]*')
        if pat.fullmatch(ab) is None:
            msg = (
                f"Representation string {ab} contains characters other than 'a' or 'b'"
            )
            raise ValueError(msg)
        rep = ''
        r0, r1 = '0', '1'
        n = 1
        try:
            it = iter(ab)
            r0 = next(it)
            while r1 := next(it):
                if r0 == r1:
                    n += 1
                    continue
                if n % 2:
                    rep += r0
                    r0 = r1
                    n = 1
        except StopIteration:
            if r0 == '0':
                pass
            elif r1 == '1' or n % 2 == 1:
                rep += r0
        self._rep = rep
        self._hash = hash(rep)

    def __hash__(self) -> int:
        return self._hash

    def __len__(self) -> int:
        return len(self._rep)

    def __str__(self) -> str:
        return f"AB('{str(self._rep)}')"

    def __eq__(self, right: object) -> bool:
        if not isinstance(right, type(self)):
            return NotImplemented
        if self._rep == right._rep:
            return True
        return False

    def __mul__(self, right: Self) -> 'AB':
        if len(self) > 0 and len(right) > 0 and self._rep[-1] == right._rep[0]:
            return AB(self._rep[0:-1]) * AB(right._rep[1:])
        return AB(self._rep + right._rep)


def ab_mult(left: AB, right: AB) -> AB:
    return left * right


# Define an algebra where consecutive elements don't repeat

ab_alg = Monoid[AB](mult=ab_mult, one=AB(''))


## Test above infrastructure


class TestAB:
    def test_equality_identity(self) -> None:
        assert AB('') == AB('')
        assert AB('') is not AB('')
        assert AB('aaabb') == AB('a')
        assert AB('aaabb') is not AB('a')

    def test_mult(self) -> None:
        assert AB('') * AB('') == AB('')
        assert AB('') * AB('abab') == AB('abab')
        assert AB('baba') * AB('') == AB('bbbabaaa')
        assert str(AB('baaa')) == "AB('ba')"
        assert str(AB('baa')) == "AB('b')"
        assert str(AB('baaa') * AB('baa')) == "AB('bab')"
        assert AB('baaa') * AB('baa') == AB('bab')


class TestMonoidAB:
    def test_equality_identity(self) -> None:
        assert ab_alg(AB('')) == ab_alg(AB(''))
        assert ab_alg(AB('')) is ab_alg(AB(''))
        assert ab_alg(AB('abbbbaaaab')) == ab_alg(AB('aaabaabbbb'))
        assert ab_alg(AB('abbbbaaaab')) is ab_alg(AB('aaabaabbbb'))
        assert ab_alg(AB('abbaaaab')) is ab_alg(AB('abaabb'))

    def test_mult(self) -> None:
        assert ab_alg(AB('')) * ab_alg(AB('')) == ab_alg(AB(''))
        assert ab_alg(AB('')) * ab_alg(AB('abab')) == ab_alg(AB('abab'))

        assert str(ab_alg(AB('baba'))) == "MonoidElement<AB('baba')>"
        assert str(ab_alg(AB(''))) == "MonoidElement<AB('')>"
        assert str(ab_alg(AB('baba')) * ab_alg(AB(''))) == "MonoidElement<AB('baba')>"
        assert str(ab_alg(AB('baaa'))) == "MonoidElement<AB('ba')>"
        assert str(ab_alg(AB('bbbabbbbbaaa'))) == "MonoidElement<AB('baba')>"

        assert ab_alg(AB('baba')) * ab_alg(AB('')) == ab_alg(AB('bbbabbbbbaaa'))
        assert ab_alg(AB('baaa')) * ab_alg(AB('aabb')) * ab_alg(AB('b')) == ab_alg(
            AB('bab')
        )
        assert ab_alg(AB('')) * ab_alg(AB('')) is ab_alg(AB(''))
        assert ab_alg(AB('')) * ab_alg(AB('abab')) is ab_alg(AB('abab'))
        assert ab_alg(AB('baba')) * ab_alg(AB('')) is ab_alg(AB('bbbabaaa'))
        assert ab_alg(AB('baaa')) * ab_alg(AB('aaababbb')) is ab_alg(AB('ab'))

    def test_pow_int(self) -> None:
        zero = ab_alg(AB(''))
        a = ab_alg(AB('a'))
        b = ab_alg(AB('b'))
        ab = ab_alg(AB('ab'))
        ba = ab_alg(AB('ba'))

        assert zero**0 == zero
        assert a**0 == zero
        assert ab**0 == zero
        assert a**3 == a

        assert a() == AB('a')

        assert (a * b)() == AB('ab')

        assert str(a) == "MonoidElement<AB('a')>"
        assert str(ab) == "MonoidElement<AB('ab')>"
        assert str(a * b) == "MonoidElement<AB('ab')>"
        assert str(ab * a) == "MonoidElement<AB('aba')>"
        assert str(ab**2) == "MonoidElement<AB('abab')>"
        assert str(ab**0) == "MonoidElement<AB('')>"

        assert (a * b) ** 4 == ab**4
        assert (a * b) ** 5 == ab**5
        assert str((a**3) * (b**2)) == "MonoidElement<AB('a')>"
        assert str(a**3 * b**2) == "MonoidElement<AB('a')>"
        assert (a**3) * (b**5) == ab
        assert b * ab**2 == ba**2 * b == b * a * b * a * b
