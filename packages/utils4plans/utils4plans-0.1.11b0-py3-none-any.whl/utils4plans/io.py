from pathlib import Path
import json
import pickle
from typing import Callable

import networkx as nx
from utils4plans.printing import StyledConsole
import tomli_w
import tomllib
from datetime import datetime


# def create_date_string():
#     p = ZonedDateTime.now_in_system_tz()
#     return str(p.date()).replace("-", "")


def create_date_string():
    n = datetime.now()
    return n.strftime("%y%m%d")


def create_time_string():
    n = datetime.now()
    return n.strftime("%y%m%d_%H%M")


class NotImplementedError(Exception):
    pass


def make_json_name(name: str):
    return f"{name}.json"


def make_pickle_name(name: str):
    return f"{name}.pickle"


def make_toml_name(name: str):
    return f"{name}.toml"


def deconstruct_path(path: Path):
    return (path.parent.parent, path.parent, path.name)


def get_path_str(path: Path):
    return f"{path.parent.name}/{path.name}"


def check_folder_exists_and_return(p: Path):
    try:
        assert p.exists(), StyledConsole.print(
            f"[bold]{get_path_str(p)}  does not exist"
        )
    except AssertionError:
        assert p.parent.exists(), StyledConsole.print(
            f"[bold]{get_path_str(p.parent)}does not exist",
        )
    return p


def get_or_make_folder_path(path: Path):
    root, parent, current = deconstruct_path(path)
    if not root.exists():
        raise Exception(f"Root does not exist: {root}")
    if not parent.exists():
        parent.mkdir()
    if not path.exists():
        if not path.suffix:
            # assume its a folder
            path.mkdir()
    # otherwise its a file and it will be created when we write to it
    return path

    # # TODO try using pathlib's walk function instead..
    # assert root_path.exists()
    # path_to_outputs = root_path / folder_name
    # if not path_to_outputs.exists():
    #     path_to_outputs.mkdir()
    # return path_to_outputs


def error_if_file_exists(path: Path):
    if path.exists():
        raise Exception(f"File already exists at {path} - try another name")
    return path


def handle_write_logic(p: Path, OVERWRITE=False):
    if OVERWRITE:
        try:
            path = check_folder_exists_and_return(p)
            StyledConsole.print(
                f"Going to overwrite {get_path_str(p)}", style="warning"
            )
            return path
        except AssertionError:
            path = get_or_make_folder_path(p)
            return p
    else:
        path = error_if_file_exists(p)
        return path


def append_if_file_exists(p: Path):
    pass


def write_graph(G: nx.Graph, folder_path: Path, name: str):
    G_json = nx.node_link_data(G, edges="edges")  # pyright: ignore[reportCallIssue]
    with open(folder_path / f"{name}.json", "w+") as file:
        json.dump(G_json, default=str, fp=file)


def read_graph(folder_path: Path, name: str):
    with open(folder_path / f"{name}.json", "r") as file:
        d = json.load(file)
    G: nx.Graph = nx.node_link_graph(
        d, edges="edges"
    )  # pyright: ignore[reportCallIssue]
    return G


def handle_folder_path(
    folder_path: Path, fx: Callable[[str], str], file_stem: str = ""
):
    if file_stem:
        p = folder_path / fx(file_stem)
    else:
        p = folder_path
    return p


def write_pickle(item, folder_path: Path, file_stem: str = "", OVERWRITE=False):
    p = handle_folder_path(folder_path, make_pickle_name, file_stem)
    path = handle_write_logic(p, OVERWRITE)
    with open(path, "wb") as handle:
        pickle.dump(item, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Wrote pickle to {path.parent} / {path.name}")


def read_pickle(folder_path: Path, file_stem: str = ""):
    p = handle_folder_path(folder_path, make_pickle_name, file_stem)
    with open(p, "rb") as handle:
        result = pickle.load(handle)
    return result


def write_json(item, folder_path: Path, file_stem: str = "", OVERWRITE=False):
    p = handle_folder_path(folder_path, make_json_name, file_stem)
    path = handle_write_logic(p, OVERWRITE)
    with open(path, "w+") as handle:
        json.dump(item, handle)
    print(f"Wrote to {path}")


def read_json(folder_path: Path, file_stem: str = ""):
    p = handle_folder_path(folder_path, make_json_name, file_stem)
    path = check_folder_exists_and_return(p)
    assert path.suffix == ".json"

    with open(path) as f:
        res = json.load(f)
    return res


def write_toml(item: dict, folder_path: Path, file_stem: str):
    p = folder_path / make_toml_name(file_stem)
    path = handle_write_logic(p, OVERWRITE=True)
    with open(path, "wb") as f:
        tomli_w.dump(item, f)


def read_toml(path_to_inputs: Path, file_stem_: str):
    file_stem = Path(file_stem_)
    if file_stem.suffix != ".toml":
        file_stem = Path(make_toml_name(file_stem.stem))

    path = check_folder_exists_and_return(path_to_inputs / file_stem)
    with open(path, "rb") as f:
        res = tomllib.load(f)
    return res


THROWAWAY_FOLDER = Path(
    "/Users/julietnwagwuume-ezeoke/_UILCode/gqe-phd/fpopt/utils4plans/throwaway"
)

if __name__ == "__main__":
    obj = {"hi": 1000000, "bye": [1, 2, 3, 4], "see": {"hi": "bye", 10: None}}
    write_json(obj, THROWAWAY_FOLDER, "test1", OVERWRITE=True)
    r = read_json(THROWAWAY_FOLDER, "test1")
    print(r)
