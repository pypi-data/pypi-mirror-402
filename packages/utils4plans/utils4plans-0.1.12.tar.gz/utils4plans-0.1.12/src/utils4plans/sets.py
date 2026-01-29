from typing import Iterable, TypeVar

T = TypeVar("T")


def set_difference(a: Iterable[T], b: Iterable[T]) -> list[T]:
    return list(set(a).difference(set(b)))


def set_intersection(a: Iterable[T], b: Iterable[T]) -> list[T]:
    return list(set(a).intersection(set(b)))


def set_equality(a: Iterable[T], b: Iterable[T]) -> bool:
    return set(a) == set(b)
