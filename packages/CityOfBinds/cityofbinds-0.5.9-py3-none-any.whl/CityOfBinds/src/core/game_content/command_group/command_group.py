from typing import Self

from ...._configs.constants import GameConstants
from ...._configs.maps import MovementMaps
from ..utils.game_strings import _CommandString
from ..utils.power import _Power
from ..utils.slash_command import _SlashCommand


class CommandGroup(_CommandString):
    """
    Manages an ordered collection of slash commands for City of Heroes/Villains binds.

    A CommandGroup provides a fluent interface for building sequences of game commands
    that can be executed together in binds. It supports power commands, movement commands,
    bind file operations, emotes, and arbitrary slash commands.

    The CommandGroup automatically handles command formatting, validation, and provides
    convenient methods for common command patterns. All commands are stored as _Command
    objects internally and can be inserted at any position using optional index parameters.

    Key Features:
        - Fluent interface with method chaining
        - Optional index parameter for precise command positioning
        - Automatic power name validation and formatting
        - Support for all major command categories
        - String representation ready for bind files

    Example:
        >>> cmd_group = CommandGroup()
        >>> cmd_group.add_power("hasten").add_emote("thumbsup").add_command("say ready!")
        >>> str(cmd_group)  # '"powexecname hasten$$e thumbsup$$say ready!"'

    Common Patterns:
        - Power rotation: Multiple power commands in sequence
        - Error handling: Save current, execute, restore on failure
        - Complex macros: Mix powers, emotes, and chat commands
    """

    def __init__(self, commands: list[str] = None):
        """
        Initialize a new CommandGroup with optional starting commands.

        Args:
            commands: Optional list of command strings to initialize with.
                     Each string will be wrapped in a _Command object.
            use_shortcuts: If True, generates command strings using shortcuts.

        Example:
            >>> # Empty command group
            >>> cmd_group = CommandGroup()
            >>> # Pre-populated command group
            >>> cmd_group = CommandGroup(["say hello", "powexecname hasten"])
        """
        self._commands = [_SlashCommand(cmd) for cmd in commands] if commands else []
        self.use_shortcuts = False

    # region Core Command Management Methods
    def add_command(self, command_string: str, index: int = None) -> Self:
        """
        Add a slash command to the command group.

        This is the fundamental method that all other add_* methods build upon.
        Commands are added as strings and automatically wrapped in _Command objects.

        Args:
            command_string: The slash command to add (with or without leading slash)
            index: Optional position to insert at. If None, appends to end.
                   Use 0 to prepend, len(commands) to append, or any valid index.
                   Negative indices work according to Python list behavior.

        Returns:
            Self for method chaining

        Raises:
            ValueError: If command_string is invalid

        Example:
            >>> cmd_group = CommandGroup()
            >>> cmd_group.add_command("say hello")           # Append (default)
            >>> cmd_group.add_command("say first", index=0)  # Prepend
            >>> cmd_group.add_command("say middle", index=1) # Insert at position 1
        """
        if index is None:
            return self._do_list_method("append", command_string)
        else:
            return self._do_list_method("insert", index, command_string)

    def remove_command(self, index: int) -> Self:
        """
        Remove a command from the command group by index.

        Args:
            index: Position of the command to remove. Supports negative indexing.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group = CommandGroup(["say hello", "say world"])
            >>> cmd_group.remove_command(0)
            >>> len(cmd_group)  # 1
        """
        return self._do_list_method("pop", index)

    def clear_commands(self) -> Self:
        """
        Remove all commands from the command group.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group = CommandGroup(["say hello", "say world"])
            >>> cmd_group.clear_commands()
            >>> len(cmd_group)  # 0
        """
        return self._do_list_method("clear")

    def _do_list_method(
        self, list_method_name: str, *args, command_string: str = None
    ) -> Self:
        """
        Internal helper to perform list operations on the command collection.

        This method provides a unified interface for list modifications, handling
        both operations that require command wrapping (insert, append) and those
        that don't (clear).

        Args:
            list_method_name: Name of the list method to invoke ('append', 'insert', 'clear')
            *args: Positional arguments to pass to the list method
            command_string: Command string to wrap in _Command (if applicable)

        Returns:
            Self for method chaining

        Note:
            This is an internal method used by public command management methods.
        """
        method = getattr(self._commands, list_method_name)
        if command_string is not None:
            method(*args, _SlashCommand(command_string))
        else:
            method(*args)
        return self

    # endregion

    # region Power Command Methods
    def add_power(self, power_string: str, index: int = None) -> Self:
        """
        Add a standard power execution command (powexecname).

        Creates a command that activates a power by name. This is the most common
        power execution method in City of Heroes/Villains.

        Args:
            power_string: Name of the power to execute (spaces allowed)
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Raises:
            ValueError: If power_string is invalid (non-alphabetic characters, etc.)

        Example:
            >>> cmd_group.add_power("hasten")        # "powexecname hasten"
            >>> cmd_group.add_power("build up")      # "powexecname build up"
            >>> cmd_group.add_power("heal", index=0) # Prepend heal command
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_NAME, power_string, index=index
        )

    def add_toggle_on_power(self, power_string: str, index: int = None) -> Self:
        """
        Add a toggle power activation command (powexectoggleon).

        Creates a command that specifically turns ON a toggle power. Useful for
        ensuring toggle powers are in the correct state.

        Args:
            power_string: Name of the toggle power to turn on
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_toggle_on_power("stealth")    # "powexectoggleon stealth"
            >>> cmd_group.add_toggle_on_power("dark nova")  # "powexectoggleon dark nova"
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_TOGGLE_ON, power_string, index=index
        )

    def add_toggle_off_power(self, power_string: str, index: int = None) -> Self:
        """
        Add a toggle power deactivation command (powexectoggleoff).

        Creates a command that specifically turns OFF a toggle power. Useful for
        power rotations and ensuring mutually exclusive toggles.

        Args:
            power_string: Name of the toggle power to turn off
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_toggle_off_power("stealth")     # "powexectoggleoff stealth"
            >>> cmd_group.add_toggle_off_power("black dwarf") # "powexectoggleoff black dwarf"
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_TOGGLE_OFF, power_string, index=index
        )

    def add_auto_power(self, power_string: str, index: int = None) -> Self:
        """
        Add an auto power execution command (powexecauto).

        Creates a command that sets a power to automatically execute when available.
        Commonly used for passive powers or powers you want to fire continuously.

        Args:
            power_string: Name of the power to set as auto-executing
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_auto_power("hasten")      # "powexecauto hasten"
            >>> cmd_group.add_auto_power("dark blast")  # "powexecauto dark blast"
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_AUTO, power_string, index=index
        )

    def add_loc_self_power(self, power_string: str, index: int = None) -> Self:
        """
        Add a locational power command targeting self (powexeclocation me).

        Creates a command that executes a power at your own character's location.
        Useful for area-effect powers, teleportation, or self-targeted abilities.

        Args:
            power_string: Name of the power to execute at self location
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_loc_self_power("teleport")     # "powexeclocation me teleport"
            >>> cmd_group.add_loc_self_power("rain of fire") # "powexeclocation me rain of fire"
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_LOCATION,
            power_string,
            CommandGroupConstants.LOCATION_SELF,
            index=index,
        )

    def add_loc_target_power(self, power_string: str, index: int = None) -> Self:
        """
        Add a locational power command targeting current target (powexeclocation target).

        Creates a command that executes a power at your current target's location.
        Useful for area-effect powers centered on enemies or allies.

        Args:
            power_string: Name of the power to execute at target location
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_loc_target_power("teleport")  # "powexeclocation target teleport"
            >>> cmd_group.add_loc_target_power("rain of fire")    # "powexeclocation target rain of fire"
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_LOCATION,
            power_string,
            CommandGroupConstants.LOCATION_TARGET,
            index=index,
        )

    def add_loc_cursor_power(self, power_string: str, index: int = None) -> Self:
        """
        Add a locational power command targeting cursor position (powexeclocation cursor).

        Creates a command that executes a power at the current cursor/mouse location.
        Provides precise targeting for area-effect abilities and teleportation.

        Args:
            power_string: Name of the power to execute at cursor location
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_loc_cursor_power("teleport")      # "powexeclocation cursor teleport"
            >>> cmd_group.add_loc_cursor_power("rain of fire")     # "powexeclocation cursor rain of fire"
        """
        return self._add_power_command(
            CommandGroupConstants.POWEXEC_LOCATION,
            power_string,
            CommandGroupConstants.LOCATION_CURSOR,
            index=index,
        )

    def _add_power_command(
        self,
        powexec_type: str,
        power_string: str,
        location_arg: str = None,
        index: int = None,
    ) -> Self:
        """
        Internal helper method to construct and add power commands.

        This method centralizes power command creation, handling validation,
        formatting, and insertion for all power-related methods.

        Args:
            powexec_type: The power execution command type (e.g., "powexecname")
            power_string: Name of the power to execute
            location_arg: Optional location argument for locational powers
            index: Optional position to insert at

        Returns:
            Self for method chaining

        Note:
            This is an internal method used by public power command methods.
            Power strings are validated through the _Power class.
        """
        command_string = self._build_power_command_string(
            powexec_type, power_string, location_arg
        )
        return self.add_command(command_string, index)

    def _build_power_command_string(
        self, powexec_type: str, power_string: str, argument: str = None
    ) -> str:
        """
        Internal helper method to construct power command strings.

        Validates power names and formats them into proper command syntax.
        Handles both simple power commands and locational power commands.

        Args:
            powexec_type: The power execution command type
            power_string: Name of the power (validated through _Power)
            argument: Optional argument (e.g., location for locational powers)

        Returns:
            Properly formatted power command string

        Example:
            >>> _build_power_command_string("powexecname", "hasten")
            # "powexecname hasten"
            >>> _build_power_command_string("powexeclocation", "teleport", "me")
            # "powexeclocation me teleport"
        """
        power = _Power(power_string)
        if argument:
            return f"{powexec_type} {argument} {str(power)}"
        return f"{powexec_type} {str(power)}"

    # endregion

    # region Movement Command Methods
    def add_movement(self, direction_string: str, index: int = None) -> Self:
        """
        Add a movement command for character direction control.

        Creates movement commands that control character movement in various directions.
        These are typically bound to WASD keys for standard movement controls.

        Args:
            direction_string: Direction to move - "forward", "backward", "left", "right", or "up"
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Raises:
            ValueError: If direction_string is not a valid movement direction

        Example:
            >>> cmd_group.add_movement("forward")    # "+forward"
            >>> cmd_group.add_movement("left")       # "+left"
            >>> cmd_group.add_movement("up")         # "+up"
        """
        return self._add_movement_command(direction_string, index)

    def _add_movement_command(self, direction_string: str, index: int = None) -> Self:
        """
        Internal helper method to add movement commands.

        Validates the direction string and constructs the appropriate movement command.

        Args:
            direction_string: Direction to move
            index: Optional position to insert at

        Returns:
            Self for method chaining

        Note:
            This is an internal method used by add_movement().
        """
        command_string = self._build_movement_command_string(direction_string)
        return self.add_command(command_string, index)

    def _build_movement_command_string(self, direction_string: str) -> str:
        """
        Internal helper method to construct movement command strings.

        Validates direction string against supported directions and returns
        the corresponding movement command.

        Args:
            direction_string: Direction to validate and convert

        Returns:
            Formatted movement command (e.g., "+forward", "+left")

        Raises:
            ValueError: If direction is not supported

        Note:
            Direction matching is case-insensitive.
        """
        direction = direction_string.lower()
        self._throw_error_if_wrong_direction(direction)
        return MovementMaps.DIRECTION_TO_MOVEMENT_MAP[direction]

    def _throw_error_if_wrong_direction(self, direction_string: str):
        """Validate movement direction string."""
        if direction_string not in MovementMaps.DIRECTION_TO_MOVEMENT_MAP:
            valid_directions = ", ".join(MovementMaps.DIRECTION_TO_MOVEMENT_MAP.keys())
            raise ValueError(
                f"Invalid movement direction: '{direction_string}'. "
                f"Valid directions are: {valid_directions}"
            )

    # endregion

    # region Bind File Command Methods
    def add_bind_load(self, index: int = None) -> Self:
        """
        Add a bind load command to reload all current binds.

        Creates a command that reloads the character's current bind configuration.
        Useful for refreshing binds after making changes.

        Args:
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_bind_load()  # "bindload"
        """
        return self.add_command(CommandGroupConstants.BIND_LOAD, index)

    def add_bind_load_file(self, file_path: str, index: int = None) -> Self:
        """
        Add a bind load file command to load binds from a specific file.

        Creates a command that loads bind configurations from the specified file.
        File path should be relative to the game's bind directory.

        Args:
            file_path: Path to the bind file to load (relative to bind directory)
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_bind_load_file("combat.txt")    # "bindloadfile combat.txt"
            >>> cmd_group.add_bind_load_file("pvp/arena.txt") # "bindloadfile pvp/arena.txt"
        """
        return self._add_bind_file_command(
            CommandGroupConstants.BIND_LOAD_FILE, file_path, index
        )

    def add_bind_load_file_silent(self, file_path: str, index: int = None) -> Self:
        """
        Add a silent bind load file command (no chat feedback).

        Creates a command that loads bind configurations from the specified file
        without displaying confirmation messages in the chat window.

        Args:
            file_path: Path to the bind file to load (relative to bind directory)
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_bind_load_file_silent("stealth.txt")  # "bindloadfilesilent stealth.txt"
        """
        return self._add_bind_file_command(
            CommandGroupConstants.BIND_LOAD_FILE_SILENT, file_path, index
        )

    def add_bind_save(self, index: int = None) -> Self:
        """
        Add a bind save command to save current binds.

        Creates a command that saves the character's current bind configuration
        to the default location.

        Args:
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_bind_save()  # "bindsave"

        Note:
            This command may need verification for current game compatibility.
        """
        return self.add_command(CommandGroupConstants.BIND_SAVE, index)

    def add_bind_save_file(self, file_path: str, index: int = None) -> Self:
        """
        Add a bind save file command to save binds to a specific file.

        Creates a command that saves the current bind configuration to the
        specified file path.

        Args:
            file_path: Path where the bind file should be saved (relative to bind directory)
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_bind_save_file("backup.txt")     # "bindsavefile backup.txt"
            >>> cmd_group.add_bind_save_file("builds/tank.txt") # "bindsavefile builds/tank.txt"
        """
        return self._add_bind_file_command(
            CommandGroupConstants.BIND_SAVE_FILE, file_path, index
        )

    def add_bind_save_file_silent(self, file_path: str, index: int = None) -> Self:
        """
        Add a silent bind save file command (no chat feedback).

        Creates a command that saves the current bind configuration to the
        specified file without displaying confirmation messages in chat.

        Args:
            file_path: Path where the bind file should be saved (relative to bind directory)
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_bind_save_file_silent("auto_backup.txt")  # "bindsavefilesilent auto_backup.txt"
        """
        return self._add_bind_file_command(
            CommandGroupConstants.BIND_SAVE_FILE_SILENT, file_path, index
        )

    def _add_bind_file_command(
        self, bind_file_command: str, bind_file_path: str, index: int = None
    ) -> Self:
        """
        Internal helper method to construct and add bind file commands.

        Args:
            bind_file_command: The bind file command type
            bind_file_path: Path to the bind file
            index: Optional position to insert at

        Returns:
            Self for method chaining

        Note:
            This is an internal method used by public bind file command methods.
        """
        command_string = self._build_bind_file_command_string(
            bind_file_command, bind_file_path
        )
        return self.add_command(command_string, index)

    def _build_bind_file_command_string(
        self, bind_file_command: str, bind_file_path: str
    ) -> str:
        """
        Internal helper method to construct bind file command strings.

        Args:
            bind_file_command: The command type (e.g., "bindloadfile")
            bind_file_path: The file path argument

        Returns:
            Formatted bind file command string

        Example:
            >>> _build_bind_file_command_string("bindloadfile", "combat.txt")
            # "bindloadfile combat.txt"
        """
        return f"{bind_file_command} {bind_file_path}"

    # endregion

    # region Emote Command Methods
    def add_emote(self, emote_string: str, index: int = None) -> Self:
        """
        Add an emote command to make the character perform an emote.

        Creates a command that triggers character emotes/animations. Emotes are
        visual expressions that can enhance role-playing and communication.

        Args:
            emote_string: Name of the emote to perform (e.g., "wave", "dance", "bow")
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Example:
            >>> cmd_group.add_emote("wave")      # "e wave"
            >>> cmd_group.add_emote("eat")       # "e eat"
            >>> cmd_group.add_emote("dance")     # "e dance"
        """
        return self.add_command(f"{CommandGroupConstants.EMOTE} {emote_string}", index)

    def add_cc_emote(self, emote_string: str, cc_slot: int, index: int = None) -> Self:
        """
        Add a costume change emote command.

        Creates a command that performs a costume change with an accompanying emote.
        Allows characters to switch between different costume slots while performing
        a visual animation.

        Args:
            emote_string: Name of the emote to perform during costume change
            cc_slot: Costume slot number to change to (0-9)
            index: Optional position to insert at. If None, appends to end.

        Returns:
            Self for method chaining

        Raises:
            ValueError: If cc_slot is not between 0 and 9

        Example:
            >>> cmd_group.add_cc_emote("spin", 1)      # "cce 1 spin"
            >>> cmd_group.add_cc_emote("backflip", 2)  # "cce 2 backflip"
        """
        if cc_slot < 0 or cc_slot > 9:
            raise ValueError("CC slot must be between 0 and 9.")
        return self.add_command(
            f"{CommandGroupConstants.CC_EMOTE} {cc_slot} {emote_string}", index
        )

    # endregion

    # region String Building and Output Methods
    def get_str(self) -> str:
        """Return the command string ready for use in bind files."""
        return self._build_command_string()

    def _build_command_string(self) -> str:
        """
        Return the command string ready for use in bind files.

        This is the primary output method that produces the formatted command string
        suitable for use in City of Heroes/Villains bind files.

        Returns:
            Formatted command string in quotes with $$ separators

        Example:
            >>> cmd_group = CommandGroup(["say hello", "powexecname hasten"])
            >>> str(cmd_group)  # '"say hello$$powexecname hasten"'
        """
        return self._build_command_string_from_components(self._commands)

    def _build_command_string_from_components(
        self, commands: list[_SlashCommand]
    ) -> str:
        if self.use_shortcuts:
            return f'"{GameConstants.COMMANDS_DELIM.join(cmd.get_short_str() for cmd in commands)}"'
        return f'"{GameConstants.COMMANDS_DELIM.join(str(cmd) for cmd in commands)}"'

    # endregion

    # region Magic Methods and Collection Interface
    def __iter__(self):
        """Enable iteration over commands."""
        return iter(self._commands)

    def __getitem__(self, index):
        """Enable index-based access to commands."""
        return self._commands[index]

    def __setitem__(self, index, value):
        """Enable index-based assignment of commands."""
        self._commands[index] = _SlashCommand(value)

    def __len__(self):
        """Return number of commands."""
        return len(self._commands)

    def __add__(self, other: "CommandGroup") -> Self:
        """
        Enable concatenation of CommandGroups using the + operator.

        Creates a new CommandGroup containing commands from both groups.
        The original CommandGroups are not modified.

        Args:
            other: Another CommandGroup to concatenate with

        Returns:
            New CommandGroup containing commands from both groups

        Example:
            >>> group1 = CommandGroup(["say hello"])
            >>> group2 = CommandGroup(["say world"])
            >>> combined = group1 + group2
            >>> len(combined)  # 2
        """
        new_command_group = self.__class__()  # Creates same type as caller
        new_command_group._commands = self._commands + other._commands
        return new_command_group

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation of the CommandGroup.

        Returns:
            String showing class name and internal command list

        Example:
            >>> group = CommandGroup(["say hello"])
            >>> repr(group)  # "_CommandGroup(commands=[_Command('say hello')])"
        """
        return f"{self.__class__.__name__}(commands={self._commands})"

    # endregion


class CommandGroupConstants:
    """
    Constants defining slash commands and mappings for City of Heroes/Villains.

    This class centralizes all command strings, arguments, and mappings used by
    CommandGroup to ensure consistency and provide a single point of maintenance
    for game command syntax.

    Categories:
        - Power execution commands (powexecname, powexectoggleon, etc.)
        - Location power arguments (me, target, cursor)
        - Bind file management commands (bindload, bindsave, etc.)
        - Emote commands (e, cce)
        - Movement direction mappings (forward -> +forward, etc.)

    Note:
        These constants reflect City of Heroes/Villains command syntax as of
        the game's current state. Some commands may need verification for
        compatibility with different server implementations.
    """

    # Power execution commands
    POWEXEC_NAME = "powexecname"  # Standard power activation
    POWEXEC_TOGGLE_OFF = "powexectoggleoff"  # Explicitly turn OFF toggle powers
    POWEXEC_TOGGLE_ON = "powexectoggleon"  # Explicitly turn ON toggle powers
    POWEXEC_AUTO = "powexecauto"  # Set power to auto-execute
    POWEXEC_LOCATION = "powexeclocation"  # Execute power at specific location

    # Location power arguments
    LOCATION_SELF = "me"  # Target self location
    LOCATION_TARGET = "target"  # Target current target's location
    LOCATION_CURSOR = "cursor"  # Target cursor/mouse position

    # Bind file commands
    BIND_LOAD = "bindload"  # Reload current binds
    BIND_LOAD_FILE = "bindloadfile"  # Load binds from file
    BIND_LOAD_FILE_SILENT = "bindloadfilesilent"  # Load binds silently
    BIND_SAVE = "bindsave"  # TODO: verify if these commands still work. Should be show_bind_file? (2025/11/28)
    BIND_SAVE_FILE = "bindsavefile"  # Save binds to file
    BIND_SAVE_FILE_SILENT = "bindsavefilesilent"  # Save binds silently

    # Emote commands
    EMOTE = "e"  # Standard emote command
    CC_EMOTE = "cce"  # Costume change emote command
