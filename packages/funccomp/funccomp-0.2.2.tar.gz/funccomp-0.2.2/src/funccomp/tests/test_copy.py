import unittest
from typing import *

from funccomp.core.Composite import Composite
from funccomp.core.StarComposite import StarComposite


class TestCompositeCopy(unittest.TestCase):
    def test_copy_returns_same_type_and_equal_factors(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        def double(x: Any) -> Any:
            return x * 2

        comp: Composite
        comp_copy: Composite

        comp = Composite(inc, 2, double)
        comp_copy = comp.copy()

        # basic properties
        self.assertIsInstance(comp_copy, Composite)
        self.assertIsNot(comp, comp_copy)
        self.assertEqual(comp.factors, comp_copy.factors)

    def test_copy_is_independent_of_mutation(self: Self) -> None:
        def inc(x: Any) -> Any:
            return x + 1

        comp: Composite
        comp_copy: Composite

        comp = Composite(inc)
        comp_copy = comp.copy()

        # mutate original
        comp *= 2  # appends factor

        # original and copy should now diverge
        self.assertNotEqual(comp.factors, comp_copy.factors)
        # sanity check: both still callable
        self.assertEqual(comp_copy(1), 2)  # inc(1)
        self.assertEqual(comp(1), 3)  # inc(inc(1))


class TestStarCompositeCopy(unittest.TestCase):
    def test_copy_returns_same_type_and_equal_factors(self: Self) -> None:
        def pair(x: Any, y: Any) -> Any:
            return (x + y, x - y)

        def combine(a: Any, b: Any) -> Any:
            return a * b

        sc: StarComposite

        sc = StarComposite(combine, pair)
        sc_copy = sc.copy()

        self.assertIsInstance(sc_copy, StarComposite)
        self.assertIsNot(sc, sc_copy)
        self.assertEqual(sc.factors, sc_copy.factors)

    def test_copy_is_independent_of_mutation(self: Self) -> None:
        def pair(x: Any, y: Any) -> Any:
            return (x + y, x - y)

        sc: StarComposite
        sc_copy: StarComposite

        sc = StarComposite(pair)
        sc_copy = sc.copy()

        sc **= 2  # mutate original

        self.assertNotEqual(sc.factors, sc_copy.factors)
        # sanity calls
        self.assertEqual(sc_copy(3, 1), (4, 2))
        self.assertEqual(
            sc(3, 1), (6, 2)
        )  # multiplied by 2 inside StarComposite semantics


if __name__ == "__main__":
    unittest.main()
