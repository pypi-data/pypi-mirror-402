from .....utils.string_thing import _StringThing
from ...._configs.valid_input import VALID_SLASH_COMMAND_PREFIXES, VALID_SLASH_COMMANDS


class _SlashCommand(_StringThing):
    ### Initialization
    def __init__(self, command: str):
        """Initialize the command with a string."""
        self._prefix = None
        self._slash_command = None
        self._args = None

        command = self._normalize_command_string(command)
        prefix, slash_command, args = self._get_command_parts(command)
        self.prefix = prefix
        self.slash_command = slash_command
        self.args = args

    # region Command Properties
    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: str):
        self._prefix = self._normalize_and_validate_prefix(prefix)

    @property
    def slash_command(self) -> str:
        return self._slash_command

    @slash_command.setter
    def slash_command(self, slash_command: str):
        self._slash_command = self._normalize_and_validate_slash_command(slash_command)

    @property
    def shortcut(self) -> str:
        """Return the shortest version of the command."""
        return VALID_SLASH_COMMANDS[self._slash_command]

    @property
    def args(self) -> str:
        return self._args

    @args.setter
    def args(self, args: str):
        self._args = self._normalize_and_validate_args(args)

    def clear_prefix(self):
        self._prefix = ""

    def get_str(self) -> str:
        """Return the command string ready for use in bind files."""
        return self._build_command_string_from_components(
            self.prefix, self.slash_command, self.args
        )

    def get_short_str(self) -> str:
        """Return the shortest version of the command string."""
        return self._build_command_string_from_components(
            self.prefix, self.shortcut, self.args
        )

    def _build_command_string_from_components(
        self, prefix: str, slash_command: str, args: str
    ) -> str:
        if args:
            return f"{prefix}{slash_command} {args}"
        else:
            return f"{prefix}{slash_command}"

    # endregion

    # region Helper Functions
    def _get_command_parts(self, command_string: str) -> tuple[str, str, str]:
        """Helper function to extract the command parts from the command string."""
        prefix = self._get_prefix_from_command_string(command_string)
        slash_command = self._get_slash_command_from_command_string(command_string)
        args = self._get_args_from_command_string(command_string)
        return prefix, slash_command, args

    def _get_prefix_from_command_string(self, command_string: str) -> str:
        """Helper function to extract the prefix from the command string."""
        for prefix in sorted(VALID_SLASH_COMMAND_PREFIXES, key=len, reverse=True):
            if command_string.startswith(prefix):
                return prefix
        return ""

    def _get_slash_command_from_command_string(self, command_string: str) -> str:
        """Helper function to extract the command from the command string."""
        slash_command = command_string.split(" ")[0]
        slash_command = self._remove_prefixes(slash_command)
        return slash_command

    def _remove_prefixes(self, slash_command: str) -> str:
        for prefix in sorted(VALID_SLASH_COMMAND_PREFIXES, key=len, reverse=True):
            if slash_command.startswith(prefix):
                return slash_command[len(prefix) :]
        return slash_command

    def _get_args_from_command_string(self, command_string: str) -> str:
        slash_command, space, args = command_string.partition(" ")
        return args if space else ""

    def _normalize_and_validate_prefix(self, prefix: str) -> str:
        prefix = self._normalize_prefix(prefix)
        self._throw_error_if_invalid_prefix(prefix)
        return prefix

    def _normalize_and_validate_slash_command(self, slash_command: str) -> str:
        slash_command = self._normalize_slash_command(slash_command)
        self._throw_error_if_unknown_slash_command(slash_command)
        return slash_command

    def _normalize_and_validate_args(self, args: str) -> str:
        return self._normalize_args(args)

    def _normalize_command_string(self, command_string: str) -> str:
        return command_string.lstrip()

    def _normalize_prefix(self, prefix: str) -> str:
        return prefix.strip()

    def _normalize_slash_command(self, slash_command: str) -> str:
        slash_command = slash_command.strip()
        slash_command = slash_command.replace("_", "")
        slash_command = slash_command.lower()
        return slash_command

    def _normalize_args(self, args: str) -> str:
        return args.lstrip()

    # endregion

    # region Error Checking Methods
    def _throw_error_if_invalid_prefix(self, prefix: str):
        """Validate prefix portion of command string."""
        if prefix and prefix not in VALID_SLASH_COMMAND_PREFIXES:
            raise ValueError(
                f"Invalid prefix '{prefix}'. Valid prefixes are: {', '.join(VALID_SLASH_COMMAND_PREFIXES)}"
            )

    def _throw_error_if_unknown_slash_command(self, slash_command: str):
        """Validate command portion of command string."""
        if slash_command not in VALID_SLASH_COMMANDS:
            raise ValueError(
                f"Unknown slash command '{slash_command}'. Please see https://homecoming.wiki/wiki/List_of_Slash_Commands for a list of valid commands."
            )

    # endregion

    # region Dunder Methods
    def __repr__(self):
        if self.args:
            return f"{self.__class__.__name__}(command='{self.slash_command}', args='{self.args}')"
        else:
            return f"{self.__class__.__name__}(command='{self.slash_command}')"

    # endregion
