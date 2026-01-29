import operator
from typing import *

from .BaseComposite import BaseComposite

__all__ = [
    "StarComposite",
]


class StarComposite(BaseComposite):
    factors: list
    __slots__ = ()

    @classmethod
    def _call(cls: type[Self], factor: Any, answer: Any) -> Any:
        if callable(factor):
            return factor(*answer)
        else:
            return operator.mul(factor, *answer)
