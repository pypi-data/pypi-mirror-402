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
from boring_math.number_theory import is_prime
from boring_math.abstract_algebra.algebras import AbelianGroup

## First define infrastructure

# Define the representation type and two functions on this type


class ModRep:
    def __init__(self, num: int, prime_mod: int):
        if prime_mod < 2:
            raise ValueError('The prime modulus must be >= 2')
        if not is_prime(prime_mod):
            raise ValueError('The prime given is not prime')
        self._num = num % prime_mod
        self._mod = prime_mod
        self._hash = hash((self._num, self._mod))

    def num(self) -> int:
        return self._num

    def mod(self) -> int:
        return self._mod

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, right: object) -> bool:
        if not isinstance(right, type(self)):
            return NotImplemented
        if self._mod != right._mod:
            return False
        if self._num == right._num:
            return True
        return False

    def __add__(self, right: Self) -> 'ModRep':
        if (mod := self._mod) != (omod := right._mod):
            msg = f'The prime moduli differ, {mod} != {omod})'
            raise ValueError(msg)
        return ModRep((self._num + right._num), mod)


def mod_add(left: ModRep, right: ModRep) -> ModRep:
    return left + right


def mod_neg(m: ModRep) -> ModRep:
    return ModRep(m.mod() - m.num(), m.mod())


# Define some values of using this representation.

i50 = ModRep(0, 5)
i51 = ModRep(1, 5)
i52 = ModRep(2, 5)
i53 = ModRep(3, 5)
i54 = ModRep(4, 5)
i55 = ModRep(5, 5)
i56 = ModRep(6, 5)
i57 = ModRep(7, 5)
i58 = ModRep(8, 5)

j50 = ModRep(0, 5)
j51 = ModRep(1, 5)
j52 = ModRep(2, 5)
j53 = ModRep(3, 5)
j54 = ModRep(4, 5)
j55 = ModRep(5, 5)
j56 = ModRep(6, 5)
j57 = ModRep(7, 5)
j58 = ModRep(8, 5)

k70 = ModRep(0, 7)
k71 = ModRep(1, 7)
k72 = ModRep(2, 7)
k73 = ModRep(3, 7)
k74 = ModRep(4, 7)
k75 = ModRep(5, 7)
k76 = ModRep(6, 7)
k77 = ModRep(7, 7)
k78 = ModRep(8, 7)

# Define 3 different Group objects, the first two isomorphic.

foo5 = AbelianGroup[ModRep](
    add=mod_add,
    zero=ModRep(0, 5),
    negate=mod_neg,
)

bar5 = AbelianGroup[ModRep](
    add=mod_add,
    zero=ModRep(0, 5),
    negate=mod_neg,
)

bar7 = AbelianGroup[ModRep](
    add=mod_add,
    zero=ModRep(0, 7),
    negate=mod_neg,
)

# Define some group elements for above group objects.

I50 = foo5(i50)
I51 = foo5(i51)
I52 = foo5(i52)
I53 = foo5(i53)
I54 = foo5(i54)
I55 = foo5(i55)
I56 = foo5(i56)
I57 = foo5(i57)
I58 = foo5(i58)

J50 = bar5(j50)
J51 = bar5(j51)
J52 = bar5(j52)
J53 = bar5(j53)
J54 = bar5(j54)
J55 = bar5(j55)
J56 = bar5(j56)
J57 = bar5(j57)
J58 = bar5(j58)

K70 = bar7(k70)
K71 = bar7(k71)
K72 = bar7(k72)
K73 = bar7(k73)
K74 = bar7(k74)
K75 = bar7(k75)
K76 = bar7(k76)
K77 = bar7(k77)
K78 = bar7(k78)


## Test above infrastructure


class TestModRep:
    def test_equality(self) -> None:
        assert i50 == i50
        assert i52 != i50
        assert i53 == j53
        assert k71 != k77
        assert k71 == k71
        assert k71 != j51
        assert K78 == K71
        assert K77 == K70

    def test_identity(self) -> None:
        assert i50 is i50
        assert i52 is not i50
        assert i53 is not j53
        assert k71 is not k77
        assert k71 is k71
        assert k71 is not j51

    def test_create(self) -> None:
        kSeventyFive = ModRep(5, 7)
        assert kSeventyFive == k75
        assert kSeventyFive is not k75


class TestGroupWithModRep:
    def test_equality(self) -> None:
        assert I50 == I50
        assert I52 != I50
        assert I53 == J53
        assert J51 != K77
        assert J51 != K71
        assert J51 != K71

    def test_identity(self) -> None:
        assert I50 is I50
        assert I52 is not I50
        assert I53 is not J53
        assert I51 is not K77
        assert I51 is not K71
        assert I51 is not J51

    def test_create(self) -> None:
        SeventyFive1 = bar7(ModRep(5, 7))
        SeventyFive2 = bar7(ModRep(5, 7))
        SeventyFive3 = bar7(ModRep(12, 7))
        assert SeventyFive1 == SeventyFive2
        assert SeventyFive2 == SeventyFive3
        assert SeventyFive3 == SeventyFive1
        assert SeventyFive1 == K75
        assert SeventyFive1 is SeventyFive2
        assert SeventyFive2 is SeventyFive3
        assert SeventyFive3 is SeventyFive1
        assert SeventyFive1 is K75


class TestGroupAdd:
    def test_add(self) -> None:
        assert I51 + I53 == I54
        assert I52 + I53 == I50
        assert I51 + I53 is I54
        assert I52 + I53 is I50

        assert K76 + K74 != K72
        assert K73 + K75 == K71
        assert K73 + K75 is K71
        assert K75 + K72 == K77 == K70
        assert K74 + K74 is K78
        assert K74 + K74 is K71
        assert K73 + K74 == K77 == K70
        assert K73 + K74 is K77
        assert K73 + K74 is K70

        assert J53 + J54 == J52
        assert J53 + J54 == I52
        assert J53 + J54 is J52
        assert J53 + J54 is not I52

    def test_bad_add(self) -> None:
        good = I54 + I54
        assert good is I53

        try:
            bad = I54 + J54
        except ValueError as err:
            assert True
            assert (
                str(err)
                == 'Addition must be between elements of the same concrete algebra'
            )
        else:
            assert bad is I51
            assert False

    def test_mult_not_implemented(self) -> None:
        good1 = I53 * 3
        assert good1 == I54
        assert good1 is I54

        good2 = 3 * I54
        assert good2 == I52
        assert good2 is I52

        try:
            bad = I54 * I54
        except TypeError as err:
            assert True
            assert str(err) == 'Element multiplication not defined on algebra'
        else:
            assert bad is I51
            assert False

        try:
            bad = I54 * J54
        except TypeError as err:
            assert True
            assert str(err) == 'Element multiplication not defined on algebra'
        else:
            assert bad is I51
            assert False
