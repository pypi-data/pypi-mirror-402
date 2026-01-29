import unittest
from typing import *

from funccomp.core.BaseComposite import BaseComposite
from funccomp.core.Composite import Composite
from funccomp.core.StarComposite import StarComposite

__all__ = ["TestSlots"]


class TestSlots(unittest.TestCase):
    def test_base_composite_has_slots(self: Self) -> None:
        self.assertTrue(hasattr(BaseComposite, "__slots__"))
        self.assertEqual(BaseComposite.__slots__, ("_factors",))

    def test_composite_is_slotted(self: Self) -> None:
        self.assertTrue(hasattr(Composite, "__slots__"))
        self.assertEqual(Composite.__slots__, ())

    def test_concrete(self: Self) -> None:
        c: Composite
        c = Composite()
        self.assertFalse(hasattr(c, "__dict__"))
        # _factors is inherited slot from BaseComposite
        c._factors = [1]
        with self.assertRaises(AttributeError):
            c.some_random_attr = "nope"

    def test_star_composite_is_slotted(self: Self) -> None:
        self.assertTrue(hasattr(StarComposite, "__slots__"))
        self.assertEqual(StarComposite.__slots__, ())

    def test_star_concrete(self: Self) -> None:
        sc: StarComposite

        sc = StarComposite()
        self.assertFalse(hasattr(sc, "__dict__"))
        sc._factors = [1]
        with self.assertRaises(AttributeError):
            sc.other_attr = "nope"


if __name__ == "__main__":
    unittest.main()
