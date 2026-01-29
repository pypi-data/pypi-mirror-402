# Copyright 2025 Geoffrey R. Scheller
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

import numpy as np
import numpy.typing as npt
from boring_math.abstract_algebra.algebras import CommutativeSemigroup
from pythonic_fp.numpy.hashable_wrapped_ndarray import HWrapNDArrayNumber as HWrap

type I64_3x3 = HWrap[npt.NDArray[np.int64]]


def matrix_add(left: I64_3x3, right: I64_3x3) -> I64_3x3:
    return HWrap(left() + right())


m3x3 = CommutativeSemigroup[I64_3x3](add=matrix_add)

np_eye = HWrap(np.eye(3, dtype=np.int64))
np_zero = HWrap(np.zeros((3, 3), dtype=np.int64))
np_A = HWrap(np.array([[5, -1, 0], [0, 2, 1], [1, 3, 1]], dtype=np.int64))
np_B = HWrap(np.array([[2, -1, 1], [1, 2 ,0], [2, 3, -1]], dtype=np.int64))
np_C = HWrap(np.array([[1, 1, -4], [1, 1, 5], [42, 0, -2]], dtype=np.int64))
np_D = HWrap(np.array([[2, -1, 0], [-1, 0, 0], [0, 0, 0]], dtype=np.int64))
np_E = HWrap(np.array([[-1, 1, 0], [1, 1, 0], [0, 0, 1]], dtype=np.int64))
np_F = HWrap(np.array([[7, -2, 1], [1, 4, 1], [3, 6, 0]], dtype=np.int64))


Eye = m3x3(np_eye)
Zero = m3x3(np_zero)
A = m3x3(np_A)
B = m3x3(np_B)
C = m3x3(np_C)
D = m3x3(np_D)
E = m3x3(np_E)
F = m3x3(np_F)


class Test_bool3:
    def test_equality(self) -> None:
        assert Eye + Zero == Eye
        assert Zero + A == A
        assert B + Zero == B
        assert Zero + Zero == Zero
        assert Zero + E == E
        assert (A + B) + C == A + (B + C)
        assert D + E == Eye
        assert A + B == F

    def test_identity(self) -> None:
        assert D + E is Eye
        assert E + D is D + E
        assert B + Zero is B
        assert Zero + F is F
        assert (A + B) + C is A + (B + C)
        assert D + E is Eye
        assert A + B is F

    def test_create(self) -> None:
        np_see = HWrap(np.array([[1, 1, -4], [1, 1, 5], [42, 0, -2]], dtype=np.int64))
        See = m3x3(np_see)
        assert See == C
        assert See is C

    def test_mult(self) -> None:
        Zero*5 == 5*Zero == Zero
        Zero*5 is Zero
        2*D + E*2 == (E+D)*2
        2*E + D*2 is 2*(D+E)
