from loguru import logger
from rich.logging import RichHandler
from rich.console import Console

DEBUG_LEVEL = "TRACE"


def make_handler(to_stderr: bool = False):
    HANDLERS = [
        {
            "sink": RichHandler(
                markup=True,
                show_time=False,
                show_path=False,
                console=Console(stderr=to_stderr),
            ),
            "format": "<cyan>{level.icon}</cyan>:<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {extra} | {message}",
        }
    ]
    return HANDLERS[0]


def logset(debug_level: str = DEBUG_LEVEL, to_stderr: bool = False):
    logger.remove()
    logger.level("START", no=22, color="<CYAN>", icon="▶▶▶▶▶▶")
    logger.level("END", no=22, color="<CYAN>", icon="◀◀◀◀◀◀")
    logger.level("SUMMARY", no=27, color="<YELLOW>", icon="%")
    # logger.add(level=DEBUG_LEVEL, **HANDLERS[0])
    logger.add(level=debug_level, **make_handler(to_stderr))

    # TODO figure out logging to individual files for each.. or snakemake..
