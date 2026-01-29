import unittest
from typing import *

from frozendict import frozendict

from funccomp.core.Composite import Composite

__all__ = ["TestComposite"]


class TestComposite(unittest.TestCase):
    # ---------- neutral elements ----------

    def test_neutral_stars0_identity(self: Self) -> None:
        c: Composite
        c = Composite(stars=0)
        self.assertEqual(c(10), 10)
        self.assertEqual(c("foo"), "foo")

    def test_neutral_stars1_antistar(self: Self) -> None:
        c: Composite
        c = Composite(stars=1)
        self.assertEqual(c(1, 2, 3), (1, 2, 3))
        self.assertEqual(c(), ())

    def test_neutral_stars2_neutral2(self: Self) -> None:
        c: Composite
        res: Any
        c = Composite(stars=2)
        res = c(a=1, b=2)
        self.assertIsInstance(res, frozendict)
        self.assertEqual(dict(res), {"a": 1, "b": 2})

    # ---------- basic composition semantics ----------

    def test_simple_composition_stars0(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        def g(x: Any) -> Any:
            return x * 2

        comp: Composite

        comp = Composite(f, g, stars=0)
        # expected: f(g(x))
        self.assertEqual(comp(3), f(g(3)))

    def test_simple_composition_stars1(self: Self) -> None:
        def g(x: Any) -> Any:
            # returns positional args for the next function
            return x, x + 1

        def f(a: Any, b: Any) -> Any:
            return a + b

        comp: Composite
        comp = Composite(f, g, stars=1)
        self.assertEqual(comp(4), f(*g(4)))

    def test_simple_composition_stars2(self: Self) -> None:
        def g(x: Any) -> dict:
            # returns keyword args for the next function
            return {"a": x, "b": x + 1}

        def f(a: Any, b: Any) -> Any:
            return a * b

        comp: Composite
        comp = Composite(f, g, stars=2)
        self.assertEqual(comp(4), f(**g(4)))

    # ---------- non-callable factor via _factor / __call__ ----------

    def test_non_callable_factor_uses_multiplication(self: Self) -> None:
        comp: Composite
        comp = Composite(2, stars=0)
        self.assertEqual(comp(3), 6)
        self.assertEqual(comp(4), 8)

    # ---------- equality, copying ----------

    def test_equality_same_factors_and_stars(self: Self) -> None:
        def f(x: Any) -> Any:
            return x

        c1: Composite
        c2: Composite

        c1 = Composite(f, stars=1)
        c2 = Composite(f, stars=1)
        self.assertEqual(c1, c2)

    def test_inequality_different_stars(self: Self) -> None:
        def f(x: Any) -> Any:
            return x

        c1: Composite
        c2: Composite

        c1 = Composite(f, stars=0)
        c2 = Composite(f, stars=1)
        self.assertNotEqual(c1, c2)

    def test_inequality_different_factors(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        def g(x: Any) -> Any:
            return x + 2

        c1: Composite
        c2: Composite

        c1 = Composite(f, stars=0)
        c2 = Composite(g, stars=0)
        self.assertNotEqual(c1, c2)

    def test_copy_creates_equal_independent_instance(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        comp: Composite
        clone: Composite

        comp = Composite(f, stars=2)
        clone = comp.copy()

        self.assertIsInstance(clone, Composite)
        self.assertEqual(comp, clone)
        self.assertIsNot(comp, clone)
        self.assertIsNot(comp.factors, clone.factors)

    # ---------- power operators ----------

    def test_pow_repeats_factors(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        comp: Composite
        func: Callable
        powered: Composite
        comp = Composite(f, stars=0)
        powered = comp**3

        self.assertIsInstance(powered, Composite)
        self.assertEqual(len(powered.factors), 3)
        for func in powered.factors:
            self.assertIs(func, f)

    def test_ipow_modifies_in_place(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        comp: Composite
        original_id: int
        comp = Composite(f, stars=0)
        original_id = id(comp)
        comp **= 2

        self.assertEqual(id(comp), original_id)
        self.assertEqual(len(comp.factors), 2)

    # ---------- repr ----------

    def test_repr_contains_class_name(self: Self) -> None:
        comp: Composite
        r: str
        comp = Composite(stars=0)
        r = repr(comp)
        self.assertIsInstance(r, str)
        self.assertIn("Composite", r)


if __name__ == "__main__":
    unittest.main()
