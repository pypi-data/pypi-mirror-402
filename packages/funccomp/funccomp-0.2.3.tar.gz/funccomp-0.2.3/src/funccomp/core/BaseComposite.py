import operator
from abc import abstractmethod
from typing import *

import setdoc
from cmp3 import CmpABC
from copyable import Copyable
from datarepr import datarepr
from identityfunction import identityfunction

__all__ = [
    "BaseComposite",
]


class BaseComposite(CmpABC, Copyable):
    factors: list
    __slots__ = ("_factors",)

    def __call__(self: Self, *args: Any, **kwargs: Any) -> Any:
        ans: Any
        factor: Any
        if not self.factors:
            return identityfunction(*args, **kwargs)
        if callable(self.factors[-1]):
            ans = self.factors[-1](*args, **kwargs)
        else:
            ans = operator.mul(self.factors[-1], *args, **kwargs)
        for factor in self.factors[-2::-1]:
            ans = self._call(factor=factor, answer=ans)
        return ans

    @setdoc.basic
    def __cmp__(self: Self, other: Any) -> Any:
        if type(self) is not type(other):
            return
        try:
            if self.factors <= other.factors and other.factors <= self.factors:
                return 0
            if self.factors <= other.factors:
                return -1
            if other.factors <= self.factors:
                return 1
            return float("nan")
        except Exception:
            pass
        if self.factors == other.factors:
            return 0
        else:
            return float("nan")

    @setdoc.basic
    def __init__(self: Self, *factors: Any) -> None:
        self._factors = list(factors)

    @setdoc.basic
    def __mul__(self: Self, other: Any) -> Self:
        if type(self) is type(other):
            return type(self)(*self.factors, *other.factors)
        else:
            return type(self)(*self.factors, other)

    @setdoc.basic
    def __imul__(self: Self, other: Any) -> Self:
        if type(self) is type(other):
            self.factors.extend(other.factors)
        else:
            self.factors.append(other)
        return self

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
        return datarepr(type(self).__name__, factors=self.factors)

    @setdoc.basic
    def __rmul__(self: Self, other: Any) -> Self:
        if type(self) is type(other):
            return type(self)(*other.factors, *self.factors)
        else:
            return type(self)(other, *self.factors)

    @setdoc.basic
    def __rpow__(self: Self, other: SupportsIndex) -> Self:
        return self**other

    @classmethod
    @abstractmethod
    def _call(cls: type[Self], factor: Any, answer: Any) -> Any: ...

    def copy(self: Self) -> Self:
        return type(self)(*self.factors)

    @property
    def factors(self: Self) -> list:
        return self._factors
