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
from boring_math.abstract_algebra.algebras import Semigroup
from pythonic_fp.numpy.hashable_wrapped_ndarray import HWrapNDArrayNumber as HWrap

type I32_2x2 = HWrap[npt.NDArray[np.int32]]


def matrix_mult(left: I32_2x2, right: I32_2x2) -> I32_2x2:
    return HWrap(left() @ right())


m2x2 = Semigroup[I32_2x2](mult=matrix_mult)

np_eye = HWrap(np.eye(2, dtype=np.int32))
np_zero = HWrap(np.zeros((2, 2), dtype=np.int32))
np_A = HWrap(np.array([[5, -1], [0, 2]], dtype=np.int32))
np_B = HWrap(np.array([[2, -1], [-1, 2]], dtype=np.int32))
np_C = HWrap(np.array([[1, 1], [1, 1]], dtype=np.int32))
np_D = HWrap(np.array([[0, 1], [1, 0]], dtype=np.int32))
np_E = HWrap(np.array([[11, -7], [-2, 4]], dtype=np.int32))


Eye = m2x2(np_eye)
Zero = m2x2(np_zero)
A = m2x2(np_A)
B = m2x2(np_B)
C = m2x2(np_C)
D = m2x2(np_D)
E = m2x2(np_E)


class Test_bool3:
    def test_equality(self) -> None:
        assert Eye * Eye == Eye
        assert Eye * A == A
        assert B * Eye == B
        assert E * Zero == Zero
        assert Zero * E == Zero
        assert (A * B) * C == A * (B * C)
        assert D * D == Eye
        assert A * B == E

    def test_identity(self) -> None:
        assert Eye * Eye is Eye
        assert Eye * A is A
        assert B * Eye is B
        assert E * Zero is Zero
        assert Zero * E is Zero
        assert (A * B) * C is A * (B * C)
        assert D * D is Eye
        assert A * B is E

    def test_create(self) -> None:
        np_see = HWrap(np.array([[1, 1], [1, 1]], dtype=np.int32))
        See = m2x2(np_see)
        assert See == C
        assert See is C

    def test_pow(self) -> None:
        Eye**5 == Eye
        Eye**5 is Eye
