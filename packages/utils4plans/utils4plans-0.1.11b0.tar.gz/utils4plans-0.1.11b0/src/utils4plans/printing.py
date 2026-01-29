from rich.theme import Theme
from rich.console import Console

custom_theme = Theme(
    {
        "info": "bold cyan",
        "success": "bold green",
        "warning": "bold #ff8700",
        "error": "bold red",
    }
)
StyledConsole = Console(theme=custom_theme)

# TODO make a logger.. 