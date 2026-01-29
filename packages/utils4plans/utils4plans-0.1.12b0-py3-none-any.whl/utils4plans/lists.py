from itertools import chain, tee, groupby
from typing import Iterable, TypeVar, Callable, Any
from expression.collections import Seq 



# TODO write doc tests?

T = TypeVar("T")
def pairwise(lst: Iterable[T]) -> Iterable[tuple[T, T]]:
    "s -> (s0, s1), (s1, s2), (s2, s3), ..."
    a, b = tee(lst)
    next(b, None)
    return zip(a, b) 



def get_unique_one(lst: Iterable[T], filter_fx: Callable[ [T], Any  ]) -> T:
    res = list(filter(filter_fx, lst))
    assert len(res) == 1, f"Expected 1 result, instead got: {res}" 
    return res[0]

def chain_flatten(lst: Iterable[Iterable[T]]) -> list[T]:
    return list(chain.from_iterable(lst))

def chain_flatten_seq(lst: Iterable[Iterable[T]]):
    return Seq(list(chain.from_iterable(lst)))

def get_unique_items_in_list_keep_order(seq: Iterable):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def sort_and_group_objects_dict(
    lst: Iterable[T], fx: Callable[[T], Any]
) -> dict[Any, list[T]]:
    sorted_objs = sorted(lst, key=fx)
    d = {}
    for k, g in groupby(sorted_objs, fx):
        d[k] = [i for i in list(g)]
    return d


def sort_and_group_objects(lst: Iterable[T], fx: Callable[[T], Any]) -> list[list[T]]:
    sorted_objs = sorted(lst, key=fx)
    return [list(g) for _, g in groupby(sorted_objs, fx)]
