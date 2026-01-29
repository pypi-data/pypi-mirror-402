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

from pythonic_fp.containers.immutable_list import IList
from pythonic_fp.iterables.merging import MergeEnum


class TestImmutableList:
    """ImmutableList test suite"""

    def test_method_returns_copy(self) -> None:
        """Test guarantee"""
        il1 = IList([1, 2, 3, 4, 5, 6])
        il2 = il1.map(lambda x: x % 3)
        assert il2[2] == il2[5] == 0
        assert il1[2] is not None and il1[2] * 2 == il1[5] == 6

    def test_empty(self) -> None:
        """Test functionality"""
        il1: IList[int] = IList()
        il2: IList[int] = IList()
        assert il1 == il2
        assert il1 is not il2
        assert not il1
        assert not il2
        assert len(il1) == 0
        assert len(il2) == 0
        il3 = il1 + il2
        assert il3 == il2 == il1
        assert il3 is not il1
        assert il3 is not il2
        assert not il3
        assert len(il3) == 0
        assert isinstance(il3, IList)

    def test_indexing(self) -> None:
        il1 = IList(['Emily', 'Rachel', 'Sarah', 'Rebekah', 'Mary'])
        assert il1[2] == 'Sarah'
        assert il1[0] == 'Emily'
        assert il1[-1] == 'Mary'
        assert il1[1] == 'Rachel'
        assert il1[-2] == 'Rebekah'

    def test_slicing(self) -> None:
        il0: IList[int] = IList()
        il1: IList[int] = IList(range(0, 101, 10))
        assert il1 == IList([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        assert il1[2:7:2] == IList([20, 40, 60])
        assert il1[8:2:-2] == IList([80, 60, 40])
        assert il1[8:] == IList([80, 90, 100])
        assert il1[8:-1] == IList([80, 90])
        assert il1 == il1[:]
        assert il1[8:130] == IList([80, 90, 100])
        assert il0[2:6] == IList()

    def test_map(self) -> None:
        il0: IList[int] = IList()
        il1: IList[int] = IList(range(6))
        assert il1 == IList([0, 1, 2, 3, 4, 5])

        assert il1.map(lambda t: t * t) == IList([0, 1, 4, 9, 16, 25])
        assert il0.map(lambda t: t * t) == IList()

    def test_foldl(self) -> None:
        il0: IList[int] = IList()
        il1: IList[int] = IList(range(1, 6))
        assert il1 == IList([1, 2, 3, 4, 5])

        assert il1.foldl(lambda s, t: s * t) == 120
        assert il0.foldl(lambda s, t: s * t, default=42) == 42
        assert il1.foldl(lambda s, t: s * t, 10) == 1200
        assert il0.foldl(lambda s, t: s * t, start=10) == 10

    def test_foldr(self) -> None:
        il0: IList[int] = IList()
        il1: IList[int] = IList(range(1, 4))
        assert il1 == IList([1, 2, 3])

        assert il1.foldr(lambda t, s: s * s - t) == 48
        assert il0.foldr(lambda t, s: s * s - t, default=-1) == -1
        assert il1.foldr(lambda t, s: s * s - t, start=5) == 232323
        assert il0.foldr(lambda t, s: s * s - t, 5) == 5

        try:
            _ = il0.foldr(lambda t, s: 5 * t + 6 * s)
        except ValueError:
            assert True
        else:
            assert False

        try:
            _ = il0.foldl(lambda t, s: 5 * t + 6 * s)
        except ValueError:
            assert True
        else:
            assert False

    def test_accummulate(self) -> None:
        il0: IList[int] = IList()
        il1: IList[int] = IList(range(1, 6))
        assert il1 == IList([1, 2, 3, 4, 5])

        def add(x: int, y: int) -> int:
            return x + y

        assert il1.accummulate(add) == IList([1, 3, 6, 10, 15])
        assert il0.accummulate(add) == IList()
        assert il1.accummulate(lambda x, y: x + y, 1) == IList([1, 2, 4, 7, 11, 16])
        assert il0.accummulate(lambda x, y: x + y, 1) == IList([1])

    def test_bind(self) -> None:
        il0: IList[int] = IList()
        il1 = IList([4, 2, 3, 5])
        il2 = IList([4, 2, 0, 3])

        def ff(n: int) -> IList[int]:
            return IList(range(n))

        fm = il1.bind(ff)
        mm = il1.bind(ff, MergeEnum.Merge)
        em = il1.bind(ff, MergeEnum.Exhaust)

        assert fm == IList([0, 1, 2, 3, 0, 1, 0, 1, 2, 0, 1, 2, 3, 4])
        assert mm == IList([0, 0, 0, 0, 1, 1, 1, 1])
        assert em == IList([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4])

        fm = il2.bind(ff, MergeEnum.Concat)
        mm = il2.bind(ff, MergeEnum.Merge)
        em = il2.bind(ff, MergeEnum.Exhaust)

        assert fm == IList([0, 1, 2, 3, 0, 1, 0, 1, 2])
        assert mm == IList()
        assert em == IList([0, 0, 0, 1, 1, 1, 2, 2, 3])

        fm = il0.bind(ff, MergeEnum.Concat)
        mm = il0.bind(ff, MergeEnum.Merge)
        em = il0.bind(ff, MergeEnum.Exhaust)

        assert fm == IList()
        assert mm == IList()
        assert em == IList()
