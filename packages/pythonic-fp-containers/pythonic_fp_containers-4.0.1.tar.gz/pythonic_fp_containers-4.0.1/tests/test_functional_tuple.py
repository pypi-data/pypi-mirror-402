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

from pythonic_fp.containers.functional_tuple import FTuple as FT
from pythonic_fp.iterables.merging import MergeEnum


class TestFunctionalTuple:
    """FunctionalTuple test suite"""
    def test_method_returns_copy(self) -> None:
        """Test guarantee"""
        ft1 = FT((1, 2, 3, 4, 5, 6,))
        ft2 = ft1.map(lambda x: x % 3)
        ft3 = ft1.copy()
        assert ft2[2] == ft2[5] == 0
        assert ft1[2] is not None and ft1[2]*2 == ft1[5] == 6
        assert ft3[2] is not None and ft3[2]*2 == ft3[5] == 6

    def test_empty(self) -> None:
        """Test functionality"""
        ft1: FT[int] = FT()
        ft2: FT[int] = FT()
        assert ft1 == ft2
        assert ft1 is not ft2
        assert not ft1
        assert not ft2
        assert len(ft1) == 0
        assert len(ft2) == 0
        ft3 = ft1 + ft2
        assert ft3 == ft2 == ft1
        assert ft3 is not ft1
        assert ft3 is not ft2
        assert not ft3
        assert len(ft3) == 0
        assert isinstance(ft3, FT)
        ft4 = ft3.copy()
        assert ft4 == ft3
        assert ft4 is not ft3

    def test_indexing(self) -> None:
        ft1 = FT(("Emily", "Rachel", "Sarah", "Rebekah", "Mary",))
        assert ft1[2] == "Sarah"
        assert ft1[0] == "Emily"
        assert ft1[-1] == "Mary"
        assert ft1[1] == "Rachel"
        assert ft1[-2] == "Rebekah"

    def test_slicing(self) -> None:
        ft0: FT[int] = FT()
        ft1: FT[int]  = FT(range(0,101,10))
        assert ft1 == FT((0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,))
        assert ft1[2:7:2] == FT((20, 40, 60,))
        assert ft1[8:2:-2] == FT((80, 60, 40,))
        assert ft1[8:] == FT((80, 90, 100,))
        assert ft1[8:-1] == FT((80, 90,))
        assert ft1 == ft1[:]
        assert ft1[8:130] == FT((80, 90, 100,))
        assert ft0[2:6] == FT()

    def test_map(self) -> None:
        ft0: FT[int] = FT()
        ft1: FT[int]  = FT(range(6))
        assert ft1 == FT((0, 1, 2, 3, 4, 5,))

        assert ft1.map(lambda t: t*t) == FT((0, 1, 4, 9, 16, 25,))
        assert ft0.map(lambda t: t*t) == FT()

    def test_foldl(self) -> None:
        ft0: FT[int] = FT()
        ft1: FT[int]  = FT(range(1, 6))
        assert ft1 == FT((1, 2, 3, 4, 5,))

        assert ft1.foldl(lambda s, t: s*t) == 120
        assert ft0.foldl(lambda s, t: s*t, default=42) == 42
        assert ft1.foldl(lambda s, t: s*t, 10) == 1200
        assert ft0.foldl(lambda s, t: s*t, start=10) == 10

    def test_foldr(self) -> None:
        ft0: FT[int] = FT()
        ft1: FT[int]  = FT(range(1, 4))
        assert ft1 == FT((1, 2, 3,))

        assert ft1.foldr(lambda t, s: s*s - t) == 48
        assert ft0.foldr(lambda t, s: s*s - t, default = -1) == -1
        assert ft1.foldr(lambda t, s: s*s - t, start=5) == 232323
        assert ft0.foldr(lambda t, s: s*s - t, 5) == 5

        try:
            _ = ft0.foldr(lambda t, s: 5*t + 6*s)
        except ValueError:
            assert True
        else:
            assert False

        try:
            _ = ft0.foldl(lambda t, s: 5*t + 6*s)
        except ValueError:
            assert True
        else:
            assert False

    def test_accummulate(self) -> None:
        ft0: FT[int] = FT()
        ft1: FT[int]  = FT(range(1,6))
        assert ft1 == FT((1, 2, 3, 4, 5,))

        def add(x: int, y: int) -> int:
            return x + y

        assert ft1.accummulate(add) == FT((1, 3, 6, 10, 15,))
        assert ft0.accummulate(add) == FT()
        assert ft1.accummulate(lambda x, y: x+y, 1) == FT((1, 2, 4, 7, 11, 16,))
        assert ft0.accummulate(lambda x, y: x+y, 1) == FT((1,))

    def test_bind(self) -> None:
        ft0: FT[int] = FT()
        ft1 = FT((4, 2, 3, 5,))
        ft2 = FT((4, 2, 0, 3,))

        def ff(n: int) -> FT[int]:
            return FT(range(n))

        fm = ft1.bind(ff)
        mm = ft1.bind(ff, MergeEnum.Merge)
        em = ft1.bind(ff, MergeEnum.Exhaust)

        assert fm == FT((0, 1, 2, 3, 0, 1, 0, 1, 2, 0, 1, 2, 3, 4,))
        assert mm == FT((0, 0, 0, 0, 1, 1, 1, 1,))
        assert em == FT((0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4,))

        fm = ft2.bind(ff, MergeEnum.Concat)
        mm = ft2.bind(ff, MergeEnum.Merge)
        em = ft2.bind(ff, MergeEnum.Exhaust)

        assert fm == FT((0, 1, 2, 3, 0, 1, 0, 1, 2,))
        assert mm == FT()
        assert em == FT((0, 0, 0, 1, 1, 1, 2, 2, 3,))

        fm = ft0.bind(ff, MergeEnum.Concat)
        mm = ft0.bind(ff, MergeEnum.Merge)
        em = ft0.bind(ff, MergeEnum.Exhaust)

        assert fm == FT()
        assert mm == FT()
        assert em == FT()

    def test_add(self) -> None:
        foo = FT((1, 2, 3,))
        bar = FT((4, 5,))
        foobar = foo + bar
        assert foobar == FT((1, 2, 3, 4, 5,))

        baz = FT(('a', 'b',))
        foobaz = foo + baz
        assert foobaz == FT((1, 2, 3, 'a', 'b',))

    def test_mult_by_int(self) -> None:
        fb = FT(('foo', 'bar',))
        fb2 = fb * 2
        fb3 = 3 * fb

        assert fb2 == FT(('foo', 'bar', 'foo', 'bar',))
        assert fb3 == FT(('foo', 'bar', 'foo', 'bar', 'foo', 'bar',))
