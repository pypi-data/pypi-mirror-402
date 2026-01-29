from ...._configs.constants import MacroCommands
from ..command_group.commands_mixin import _CommandsMixin
from ..utils.game_strings import _CommandString


class Macro(_CommandsMixin, _CommandString):
    MACRO_COMMAND = MacroCommands.MACRO

    def __init__(self, name: str, commands: list[str] = None):
        """
        Initialize a new Macro with a name and optional commands.

        Args:
            name: Name of the macro
            commands: List of slash command strings to include in the macro
        """
        _CommandsMixin.__init__(self, commands)
        self.name = name

    def get_str(self) -> str:
        return self._build_macro_string()

    def _build_macro_string(self) -> str:
        return f'{self.MACRO_COMMAND} "{self.name}" {self.commands}'
