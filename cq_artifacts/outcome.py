"""Typed success or failure for pure cores.

Callers branch with ``isinstance``. There is no bind/map chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E


type Result[T, E] = Ok[T] | Err[E]
