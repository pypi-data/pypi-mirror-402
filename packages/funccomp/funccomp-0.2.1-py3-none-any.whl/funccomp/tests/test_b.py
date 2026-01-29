import unittest
from typing import *

from funccomp.core.Composite import Composite
from funccomp.core.StarComposite import StarComposite


class TestBaseComposite(unittest.TestCase):
    def test_init_stores_factors(self: Self) -> None:
        f: Callable
        g: Callable
        base: Composite
        f = lambda x: x + 1
        g = lambda x: x * 2
        base = Composite(f, g)
        self.assertEqual(base.factors, [f, g])

    def test_cmp_equal_same_factors(self: Self) -> None:
        def f(x: Any) -> Any:
            return x

        c1: Composite
        c2: Composite
        c1 = Composite(f)
        c2 = Composite(f)
        # Directly testing __cmp__ to avoid depending on CmpABC details
        self.assertEqual(c1.__cmp__(c2), 0)

    def test_pow_creates_repeated_factors(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        comp: Composite
        comp3: Composite

        comp = Composite(f)
        comp3 = comp**3

        self.assertEqual(comp3.factors, [f, f, f])
        self.assertEqual(comp3(0), 3)  # f(f(f(0))) = 3

    def test_ipow_in_place_repetition(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        comp: Composite
        ref: Composite

        comp = Composite(f)
        ref = comp
        comp **= 2

        self.assertIs(comp, ref)
        self.assertEqual(comp.factors, [f, f])
        self.assertEqual(comp(0), 2)


class TestComposite(unittest.TestCase):
    def test_single_function(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        comp: Composite

        comp = Composite(inc)
        self.assertEqual(comp(3), 4)

    def test_two_functions_composed_order(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        def double(x: Any) -> Any:
            return x * 2

        comp: Composite
        # factors = [inc, double]
        comp = Composite(inc, double)

        # __call__: last factor (double) first, then inc
        # so inc(double(x)) = 2*x + 1
        self.assertEqual(comp(3), 7)

    def test_constant_and_function(self: Self) -> None:
        def double(x: Any) -> Any:
            return x * 2

        comp: Composite
        comp2: Composite
        # factors = [2, double] ⇒ 2 * double(x)
        comp = Composite(2, double)
        self.assertEqual(comp(3), 12)

        # factors = [double, 2] ⇒ double(2 * x)
        comp2 = Composite(double, 2)
        self.assertEqual(comp2(3), 12)

    def test_mul_with_same_type_appends_factors(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        def double(x: Any) -> Any:
            return x * 2

        c1: Composite
        c2: Composite
        c3: Composite

        c1 = Composite(inc)
        c2 = Composite(double)
        c3 = c1 * c2

        self.assertEqual(c3.factors, [inc, double])
        self.assertEqual(c3(3), 7)  # inc(double(3))

    def test_mul_with_other_adds_other_as_factor(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        c: Composite
        c2: Composite

        c = Composite(inc)
        c2 = c * 2

        # factors = [inc, 2]; __call__ does 2 * inc(x)
        self.assertEqual(c2.factors, [inc, 2])
        self.assertEqual(c2(3), 7)  # 2 * 3 + 1

    def test_rmul_with_other_adds_other_on_left(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        c: Composite
        c2: Composite

        c = Composite(inc)
        c2 = 2 * c

        # factors = [2, inc]; __call__ does inc(2 * x)
        self.assertEqual(c2.factors, [2, inc])
        self.assertEqual(c2(3), 8)  # 2 * (3 + 1)

    def test_imul_in_place_with_same_type(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        def double(x: Any) -> Any:
            return x * 2

        c1: Composite
        c2: Composite
        ref: Composite

        c1 = Composite(inc)
        c2 = Composite(double)

        ref = c1
        c1 *= c2

        self.assertIs(c1, ref)
        self.assertEqual(c1.factors, [inc, double])
        self.assertEqual(c1(3), 7)

    def test_imul_in_place_with_other(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        c: Composite
        ref: Composite

        c = Composite(inc)
        ref = c
        c *= 2

        self.assertIs(c, ref)
        self.assertEqual(c.factors, [inc, 2])
        self.assertEqual(c(3), 7)


class TestStarComposite(unittest.TestCase):
    def test_star_composite_multi_arg_pipeline(self: Self) -> None:
        # compute_pair runs first (last factor), then combine uses its outputs
        def compute_pair(x: Any, y: Any) -> tuple:
            return (x + y, x - y)

        def combine(a: Any, b: Any) -> Any:
            return a * b

        sc: StarComposite

        sc = StarComposite(combine, compute_pair)
        # __call__: compute_pair(2, 3) -> (5, -1)
        # then combine(*answer) -> combine(5, -1) -> -5
        self.assertEqual(sc(2, 3), -5)

    def test_star_composite_single_tuple_return(self: Self) -> None:
        # Last factor returns a 1-tuple; next factor sees *answer -> single arg
        def pack(x: Any, y: Any) -> tuple:
            return (x + y,)

        def square(z: Any) -> Any:
            return z * z

        sc: StarComposite

        sc = StarComposite(square, pack)
        # pack(2, 3) -> (5,), then square(*answer) -> square(5) -> 25
        self.assertEqual(sc(2, 3), 25)


if __name__ == "__main__":
    unittest.main()
