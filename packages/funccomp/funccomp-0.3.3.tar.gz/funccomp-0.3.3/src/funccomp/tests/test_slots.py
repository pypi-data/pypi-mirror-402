import unittest
from typing import *

from funccomp.core.Composite import Composite

__all__ = ["TestSlots"]


class TestSlots(unittest.TestCase):

    def test_composite_has_slots(self: Self) -> None:
        # Class-level __slots__ definition
        self.assertTrue(hasattr(Composite, "__slots__"))
        self.assertIn("_factors", Composite.__slots__)
        self.assertIn("_stars", Composite.__slots__)

    def test_composite_instance_has_no_dict(self: Self) -> None:
        c: Composite
        c = Composite()
        # Slotted instances should not have a __dict__ by default
        self.assertFalse(hasattr(c, "__dict__"))

    def test_cannot_add_new_attributes(self: Self) -> None:
        c: Composite
        c = Composite()
        with self.assertRaises(AttributeError):
            c.some_new_attr = 42


if __name__ == "__main__":
    unittest.main()
