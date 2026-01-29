from ...._configs.constants import MacroCommands
from .macro import Macro


class MacroImage(Macro):
    MACRO_COMMAND = MacroCommands.MACRO_IMAGE

    def __init__(self, image: str, tooltip: str, commands: list[str] = None):
        """
        Initialize a new Macro with a name and optional commands.

        Args:
            name: Name of the macro
            commands: List of slash command strings to include in the macro
        """
        super().__init__(tooltip, commands)
        self.tooltip = tooltip
        self.image = image

    def _build_macro_string(self) -> str:
        return f'{self.MACRO_COMMAND} "{self.image}" "{self.tooltip}" {self.commands}'

    # TODO: provide error checking for image string? (2025/12/30)
