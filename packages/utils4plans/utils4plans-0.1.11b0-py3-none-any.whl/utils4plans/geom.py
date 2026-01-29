from typing import NamedTuple
from dataclasses import dataclass
from typing import Sequence
import numpy as np


class InvalidRangeException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass(frozen=True)
class Range:
    min: float
    max: float

    def __post_init__(self):
        try:
            assert self.min <= self.max
        except AssertionError:
            raise InvalidRangeException(self.min, self.max)

    def __repr__(self) -> str:
        return f"[{self.min:.2f}, {self.max:.2f}]"

    def __eq__(self, other) -> bool:
        return np.isclose(self.min, other.min) and np.isclose(self.max, other.max)

    def size(self):
        return self.max - self.min


@dataclass(frozen=True)
class Domain:
    horz_range: Range
    vert_range: Range


class ShapelyBounds(NamedTuple):
    minx: float
    miny: float
    maxx: float
    maxy: float

    @property
    def domain(self):
        horz_range = Range(self.minx, self.maxx)
        vert_range = Range(self.miny, self.maxy)
        return Domain(horz_range, vert_range)


CoordsType = list[tuple[float | int, float | int]]


@dataclass(frozen=True, eq=True)
class Coord:
    x: float
    y: float

    def __str__(self) -> str:
        return f"({self.x:.2f}, {self.y:.2f})"

    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, Coord):
            return self.x == other.x and self.y == other.y
        else:
            raise ValueError("Invalid comparison")

    def __lt__(self, other: object, /) -> bool:
        if isinstance(other, Coord):
            return (other.x, other.y) < (self.x, self.y)
        else:
            raise ValueError("Invalid comparison")

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    @property
    def as_tuple(self):
        return (self.x, self.y)


def tuple_list_from_list_of_coords(coords: list[Coord]) -> CoordsType:
    return [i.as_tuple for i in coords]


def coords_type_list_to_coords(input_coords: CoordsType):
    return [Coord(*i) for i in input_coords]


@dataclass
class OrthoDomain:
    coords: list[Coord]
    name: str = ""

    @classmethod
    def from_tuple_list(
        cls, coords: Sequence[tuple[float | int, float | int]], name: str = ""
    ):
        return cls([Coord(*i) for i in coords], name)

    @property
    def tuple_list(self):
        return tuple_list_from_list_of_coords(self.coords)
