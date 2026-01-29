import unittest
from typing import *
from unittest.mock import patch

from funccomp.core.Composite import Composite

__all__ = ["TestBaseComposite"]


class TestBaseComposite(unittest.TestCase):

    @patch("funccomp.core.BaseComposite.identityfunction")
    def test_call_with_no_factors_uses_identity(self: Self, mock_identity: Any) -> None:
        comp: Composite
        result: Any

        mock_identity.return_value = "identity_result"

        comp = Composite()  # no factors
        result = comp(1, 2, foo=3)

        mock_identity.assert_called_once_with(1, 2, foo=3)
        self.assertEqual(result, "identity_result")


if __name__ == "__main__":
    unittest.main()
