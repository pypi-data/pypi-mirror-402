import copy

from .command_group import CommandGroup


class _CommandsMixin:
    def __init__(self, commands: list[str] = None):
        self._commands = None
        self.commands = commands or []

    @property
    def commands(self) -> CommandGroup:
        return self._commands

    @commands.setter
    def commands(self, value):
        if isinstance(value, list):
            self._commands = CommandGroup(value)
        elif isinstance(value, CommandGroup):
            self._commands = copy.deepcopy(value)
        else:
            self._throw_set_commands_type_error(value)

    @property
    def use_shortcuts(self) -> bool:
        return self._commands.use_shortcuts

    @use_shortcuts.setter
    def use_shortcuts(self, value: bool):
        self._commands.use_shortcuts = value

    def _throw_set_commands_type_error(self, value):
        raise TypeError(
            f"Invalid type '{type(value)}'. Commands must be set using a list of strings or a CommandGroup instance."
        )
