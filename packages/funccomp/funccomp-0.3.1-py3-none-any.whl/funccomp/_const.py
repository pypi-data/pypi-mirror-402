from typing import *

from antistar import antistar
from frozendict import frozendict
from identityfunction import identityfunction

__all__ = ["NEUTRALS"]


def neutral2(**kwargs: Any) -> frozendict:
    return frozendict(kwargs)


NEUTRALS: tuple[Callable, Callable, Callable]
NEUTRALS = identityfunction, antistar, neutral2
