import networkx as nx
from dataclasses import dataclass
from typing import Generic, TypeVar, Literal, Iterable

T = TypeVar("T")


def nodes_from_edges(edges_: Iterable[tuple[T, T]]):
    edges = list(edges_)
    n1 = [i[0] for i in edges] + [edges[-1][1]]
    return n1


@dataclass
class Edge(Generic[T]):
    u: T
    v: T
    ix: int = 0
    pair_num: Literal[1, 2] = 1
    # marked=False

    @property
    def name(self):
        return f"e{self.ix},{self.pair_num}"

    @property
    def pair(self):
        return (self.u, self.v)

    def __hash__(self) -> int:
        return hash(frozenset(self.pair))

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Edge):
            return True if frozenset(value.pair) == frozenset(self.pair) else False
        raise Exception("Invalid object for comparison")


@dataclass
class EdgeList(Generic[T]):
    edges: list[Edge[T]]

    def get(self, u: T, v: T):
        matches = [i for i in self.edges if i.u == u and i.v == v]
        assert len(matches) == 1
        return matches[0]

    def find_unique(self):
        s = set(self.edges)
        assert len(s) == 0.5 * (len(self.edges))
        return s

    @classmethod
    def to_edge_list(cls, edges: Iterable):
        return cls([Edge(*i) for i in edges])


def neighborhood(G, node, n):
    # TODO do something simpler if n = 1
    path_lengths = nx.single_source_dijkstra_path_length(G, node)
    return [node for node, length in path_lengths.items() if length == n]
