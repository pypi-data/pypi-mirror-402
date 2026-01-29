import math
import unittest

from funccomp.core.Composite import Composite


class TestCompositeCmp(unittest.TestCase):
    def test_equal_same_type_and_factors(self):
        c1 = Composite(1, 2, 3)
        c2 = Composite(1, 2, 3)

        # same type, same factors
        self.assertTrue(c1 == c2)
        self.assertFalse(c1 != c2)
        # no strict ordering
        self.assertFalse(c1 < c2)
        self.assertFalse(c1 > c2)

    def test_less_and_greater_with_numeric_factors(self):
        smaller = Composite(1, 2)
        bigger = Composite(1, 2, 3)

        self.assertTrue(smaller < bigger)
        self.assertTrue(bigger > smaller)
        self.assertFalse(smaller > bigger)
        self.assertFalse(bigger < smaller)

    def test_incomparable_different_types(self):
        class OtherComposite(Composite):
            pass

        c1 = Composite(1)
        c2 = OtherComposite(1)

        # equality should be False (different types)
        self.assertFalse(c1 == c2)
        self.assertTrue(c1 != c2)

        # ordering comparisons should raise TypeError
        with self.assertRaises(TypeError):
            _ = c1 < c2
        with self.assertRaises(TypeError):
            _ = c1 > c2
        with self.assertRaises(TypeError):
            _ = c1 <= c2
        with self.assertRaises(TypeError):
            _ = c1 >= c2

    def test_raw_cmp_signs_for_sanity(self):
        c1 = Composite(1, 2)
        c2 = Composite(1, 2, 3)
        c3 = Composite(1, 2)

        r12 = c1.__cmp__(c2)
        r21 = c2.__cmp__(c1)
        r13 = c1.__cmp__(c3)

        self.assertLess(r12, 0)  # c1 < c2
        self.assertGreater(r21, 0)  # c2 > c1
        self.assertEqual(r13, 0)  # c1 == c3

        # different type → __cmp__ returns None
        class OtherComposite(Composite):
            pass

        oc = OtherComposite(1, 2)
        r_incomp = c1.__cmp__(oc)
        self.assertIsNone(r_incomp)


if __name__ == "__main__":
    unittest.main()
