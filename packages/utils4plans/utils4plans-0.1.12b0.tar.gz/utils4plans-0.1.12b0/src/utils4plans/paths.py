from utils4plans.io import check_folder_exists_and_return
from dataclasses import dataclass
from pathlib import Path
from enum import StrEnum


STATIC = "static"


class FolderStructure(StrEnum):
    INPUTS = "_01_inputs"  # svg files, pngs etc.., material info, weather..
    PLANS = "_02_plans"  # floor plans ready for energy modeling
    MODELS = "_03_models"  # energy models
    TEMP = "_04_temp"  # pickled files
    FIGURES = "_05_figures"


# add to utils later..
# TODO different options of behavior if doesnt exist..


# TODO generating filenames based on day, then increment +1, +2, etc


@dataclass(frozen=True)
class StaticPaths:
    name: str
    base_path: Path

    def get_data_folder(self, folder: FolderStructure):
        return check_folder_exists_and_return(
            self.base_path / STATIC / self.name / folder
        )

    @property
    def inputs(self):
        return self.get_data_folder(FolderStructure.INPUTS)

    @property
    def plans(self):
        return self.get_data_folder(FolderStructure.PLANS)

    @property
    def models(self):
        return self.get_data_folder(FolderStructure.MODELS)

    @property
    def figures(self):
        return self.get_data_folder(FolderStructure.FIGURES)

    @property
    def temp(self):
        return self.get_data_folder(FolderStructure.TEMP)
