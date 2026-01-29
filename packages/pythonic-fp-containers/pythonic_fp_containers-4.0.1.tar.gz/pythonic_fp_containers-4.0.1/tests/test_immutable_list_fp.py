# Copyright 2023-2024 Geoffrey R. Scheller
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

"""Test FP use cases"""

from pythonic_fp.containers.immutable_list import IList
from pythonic_fp.iterables.merging import MergeEnum


class TestFP:
    """FP test of IList with other datastructures"""
    def test_fold(self) -> None:
        """Test folding"""
        def add2(x: int, y: int) -> int:
            return x + y

        def mult2[S](x: int, y: int) -> int:
            return x * y

        il0: IList[int] = IList()
        il5: IList[int] = IList([1, 2, 3, 4, 5])

        assert il5[1] == 2
        assert il5[4] == 5

        assert il0.foldl(add2, 42) == 42
        assert il0.foldr(add2, 42) == 42
        assert il5.foldl(add2) == 15
        assert il5.foldl(add2, 0) == 15
        assert il5.foldl(add2, 10) == 25
        assert il5.foldl(mult2, 1) == 120
        assert il5.foldl(mult2, 10) == 1200
        assert il5.foldr(add2) == 15
        assert il5.foldr(add2, 0) == 15
        assert il5.foldr(add2, 10) == 25
        assert il5.foldr(mult2, 1) == 120
        assert il5.foldr(mult2, 10) == 1200
        assert il5 == IList([1, 2, 3, 4, 5])

        assert il5.accummulate(add2) == IList([1, 3, 6, 10, 15])
        assert il5.accummulate(add2, 10) == IList([10, 11, 13, 16, 20, 25])
        assert il5.accummulate(mult2) == IList([1, 2, 6, 24, 120])
        assert il0.accummulate(add2) == IList()
        assert il0.accummulate(mult2) == IList()

    def test_immutablelist_bind(self) -> None:
        """Test bind (flatmap)"""
        def l1(x: int) -> int:
            return 2*x + 1

        def l2(x: int) -> IList[int]:
            return IList(range(2, x + 1)).accummulate(lambda x, y: x + y)

        il0 = IList(range(3, 101))
        il1 = il0.map(l1)
        il2 = il0.bind(l2, MergeEnum.Concat)
        il3 = il0.bind(l2, MergeEnum.Merge)
        il4 = il0.bind(l2, MergeEnum.Exhaust)
        assert (il1[0], il1[1], il1[2], il1[-1]) == (7, 9, 11, 201)
        assert (il2[0], il2[1]) == (2, 5)
        assert (il2[2], il2[3], il2[4]) == (2, 5, 9)
        assert (il2[5], il2[6], il2[7], il2[8]) == (2, 5, 9, 14)
        assert il2[-1] == il2[4948] == 5049
        assert (il3[0], il3[1]) == (2, 2)
        assert (il3[2], il3[3]) == (2, 2)
        assert (il3[4], il3[5]) == (2, 2)
        assert (il3[96], il3[97]) == (2, 2)
        assert (il3[98], il3[99]) == (5, 5)
        assert (il4[0], il4[1], il4[2]) == (2, 2, 2)
        assert (il4[95], il4[96], il4[97]) == (2, 2, 2)
        assert (il4[98], il4[99], il4[100]) == (5, 5, 5)
        assert (il4[290], il4[291], il4[292]) == (9, 9, 9)
        assert (il4[293], il4[294], il4[295]) == (14, 14, 14)
        assert (il4[-4], il4[-3], il4[-2], il4[-1]) == (4850, 4949, 4949, 5049)
        assert il4[-1] == il4[4948] == 5049
