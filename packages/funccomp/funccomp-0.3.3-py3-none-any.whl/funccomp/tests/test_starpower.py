import unittest
from typing import *

from funccomp.core.Composite import Composite

__all__ = ["TestStarPower"]


class TestStarPower(unittest.TestCase):

    def test_pow_preserves_stars(self: Self) -> None:
        def f(x: Any) -> Any:
            return x + 1

        c: Composite
        c = Composite(f, stars=1)
        powered = c**3

        # stars should be preserved on the new instance
        self.assertEqual(powered.stars, c.stars)

    def test_rpow_preserves_stars(self: Self) -> None:
        def f(x: Any) -> Any:
            return x * 2

        c: Composite
        c = Composite(f, stars=2)
        with self.assertRaises(TypeError):
            4**c  # uses __rpow__

    def test_ipow_preserves_stars_in_place(self: Self) -> None:
        def f(x: Any) -> Any:
            return x - 1

        c: Composite
        original_id: int
        original_stars: int
        c = Composite(f, stars=1)
        original_stars = c.stars
        original_id = id(c)
        c **= 4

        # same object, factors repeated, stars unchanged
        self.assertEqual(id(c), original_id)
        self.assertEqual(c.stars, original_stars)
        self.assertEqual(len(c.factors), 4)
        self.assertTrue(all(func is f for func in c.factors))


if __name__ == "__main__":
    unittest.main()
