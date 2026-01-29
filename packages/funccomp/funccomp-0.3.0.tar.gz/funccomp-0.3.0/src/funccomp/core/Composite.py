import operator
from typing import *

import setdoc
from copyable import Copyable
from datarepr import datarepr

from funccomp import _const

__all__ = ["Composite"]


class Composite(Copyable):
    factors: list
    stars: int
    __slots__ = ("_factors", "_stars")

    def __call__(self: Self, *args: Any, **kwargs: Any) -> Any:
        ans: Any
        index: int
        if not self.factors:
            return _const.NEUTRALS[self.stars](*args, **kwargs)
        ans = self._factor(-1, *args, **kwargs)
        for index in range(-2, -1 - len(self.factors), -1):
            if self.stars == 0:
                ans = self._factor(index, ans)
            if self.stars == 1:
                ans = self._factor(index, *ans)
            if self.stars == 2:
                ans = self._factor(index, **ans)
        return ans

    @setdoc.basic
    def __eq__(self: Self, other: Any) -> Any:
        if type(self) is not type(other):
            return False
        if self.factors != other.factors:
            return False
        if self.stars != other.stars:
            return False
        return True

    @setdoc.basic
    def __init__(self: Self, *factors: Any, stars: SupportsIndex = 0) -> None:
        self._factors = list(factors)
        self.stars = stars

    @setdoc.basic
    def __pow__(self: Self, other: SupportsIndex) -> Self:
        return type(self)(*(self.factors * other))

    @setdoc.basic
    def __ipow__(self: Self, other: SupportsIndex) -> Self:
        data: list
        data = self.factors * other
        self.factors.clear()
        self.factors.extend(data)
        return self

    @setdoc.basic
    def __repr__(self: Self) -> str:
        return datarepr(
            type(self).__name__,
            *self.factors,
            stars=self.stars,
        )

    @setdoc.basic
    def __rpow__(self: Self, other: SupportsIndex) -> Self:
        return self**other

    def _factor(self: Self, index: int, /, *args: Any, **kwargs: Any) -> Any:
        if callable(self.factors[index]):
            return self.factors[index](*args, **kwargs)
        else:
            return operator.mul(self.factors[index], *args, **kwargs)

    @setdoc.basic
    def copy(self: Self) -> Self:
        return type(self)(*self.factors, stars=self.stars)

    @property
    def factors(self: Self) -> list:
        return self._factors

    @property
    def stars(self: Self) -> int:
        return self._stars

    @stars.setter
    def stars(self: Self, value: SupportsIndex) -> None:
        self._stars = operator.index(value) % 3
