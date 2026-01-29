from .....utils.templates.pool import Pool
from .....utils.templates.templates import ListTemplate
from ...game_content.command_group.command_group import (
    CommandGroup,
    CommandGroupConstants,
)
from ...game_content.utils.power import _Power
from .command_factory import _CommandFactory


class _CommandsTemplate(CommandGroup, ListTemplate):
    """
    Template for generating command groups with pool-based command variations.

    _CommandsTemplate combines command group functionality with list template capabilities
    to create dynamic command sequences with variations. It supports power pools, toggle
    commands, and arbitrary command argument pools that can generate multiple command
    variations through parallel iteration.

    The template system allows for complex command sequences where different pools of
    arguments can be combined to create comprehensive bind variations. For example,
    a power pool with multiple powers will generate different command groups for each
    power in the pool.

    Key Features:
        - Power pool management with automatic _Power object conversion
        - Toggle power support (toggle on/off/auto)
        - Generic command argument pools for custom commands
        - Parallel iteration through multiple pools using LCM calculation
        - CommandGroup generation with proper command validation

    Inheritance Chain:
        _CommandsTemplate -> _CommandGroup (command management)
                         -> ListTemplate (pool iteration and generation)

    Example:
        >>> template = _CommandsTemplate()
        >>> template.add_power_pool(["Hasten", "Super Speed"])
        >>> template.add_toggle_on_power_pool(["Combat Jumping"])
        >>> # Generates 2 variations: one with each power from the first pool
        >>> command_group = template._build_one()
        >>> len(template._get_unique_count())  # 2
    """

    def __init__(self):
        """
        Initialize a new _CommandsTemplate with empty command collections.

        Creates a template that can accumulate command pools and generate command groups
        with variations. Initializes both parent classes with the shared _commands list
        for seamless integration between command management and template generation.

        The template starts with no commands and pools must be added using the various
        add_* methods before generation can occur.

        Example:
            >>> template = _CommandsTemplate()
            >>> len(template._commands)  # 0 - no commands initially
            >>> template.add_power_pool(["Hasten"])
            >>> len(template._commands)  # 1 - one pool added
        """
        CommandGroup.__init__(self)
        ListTemplate.__init__(self, self._commands)

    # region Power Pool Methods
    def add_power_pool(self, powers: list[str]) -> "_CommandsTemplate":
        """
        Add a pool of power execution commands to the template.

        Creates a command pool where each power will generate a 'powexec_name' command
        when the template is built. The pool enables variation generation where different
        builds will use different powers from the provided list.

        Args:
            powers: List of power names to include in the pool
                   (e.g., ["Hasten", "Super Speed", "Combat Jumping"])

        Returns:
            Self for method chaining

        Example:
            >>> template = _CommandsTemplate()
            >>> template.add_power_pool(["Hasten", "Super Speed"])
            >>> # Generates: "powexec_name Hasten" and "powexec_name Super Speed" variations
            >>> template.add_power_pool(["Combat Jumping"])
            >>> # Now has 2×1=2 unique combinations

        Note:
            Power names are automatically converted to _Power objects for validation.
            Invalid power names will raise exceptions during _Power instantiation.
        """
        return self.add_command_arguments_pool(
            CommandGroupConstants.POWEXEC_NAME, [_Power(power) for power in powers]
        )

    def add_toggle_on_power_pool(self, powers: list[str]) -> "_CommandsTemplate":
        """
        Add a pool of toggle-on power commands to the template.

        Creates a command pool where each power will generate a 'powexec_toggleon' command
        for explicitly enabling toggle powers. Useful for ensuring toggle powers are
        activated regardless of their current state.

        Args:
            powers: List of toggle power names to include in the pool
                   (e.g., ["Combat Jumping", "Super Jump", "Hover"])

        Returns:
            Self for method chaining

        Example:
            >>> template = _CommandsTemplate()
            >>> template.add_toggle_on_power_pool(["Combat Jumping", "Hover"])
            >>> # Generates: "powexec_toggleon Combat Jumping" and "powexec_toggleon Hover"

        Note:
            Only works with toggle powers. Using this with click powers may result
            in game errors. Power validation occurs through _Power objects.
        """
        return self.add_command_arguments_pool(
            CommandGroupConstants.POWEXEC_TOGGLE_ON, [_Power(power) for power in powers]
        )

    def add_toggle_off_power_pool(self, powers: list[str]) -> "_CommandsTemplate":
        """
        Add a pool of toggle-off power commands to the template.

        Creates a command pool where each power will generate a 'powexec_toggleoff' command
        for explicitly disabling toggle powers. Useful for creating binds that ensure
        specific toggle powers are deactivated.

        Args:
            powers: List of toggle power names to include in the pool
                   (e.g., ["Sprint", "Rest", "Fly"])

        Returns:
            Self for method chaining

        Example:
            >>> template = _CommandsTemplate()
            >>> template.add_toggle_off_power_pool(["Sprint", "Rest"])
            >>> # Generates: "powexec_toggleoff Sprint" and "powexec_toggleoff Rest"

        Note:
            Only effective with toggle powers. Click powers cannot be toggled off.
            Power validation occurs through _Power objects.
        """
        return self.add_command_arguments_pool(
            CommandGroupConstants.POWEXEC_TOGGLE_OFF,
            [_Power(power) for power in powers],
        )

    def add_auto_power_pool(self, powers: list[str]) -> "_CommandsTemplate":
        """
        Add a pool of auto-activate power commands to the template.

        Creates a command pool where each power will generate a 'powexec_auto' command
        for setting powers to auto-activate mode. Auto powers will activate automatically
        when available and appropriate conditions are met.

        Args:
            powers: List of power names suitable for auto-activation
                   (e.g., ["Hasten", "Dull Pain", "Instant Healing"])

        Returns:
            Self for method chaining

        Example:
            >>> template = _CommandsTemplate()
            >>> template.add_auto_power_pool(["Hasten", "Dull Pain"])
            >>> # Generates: "powexec_auto Hasten" and "powexec_auto Dull Pain"

        Note:
            Auto-activation behavior depends on game AI and power recharge status.
            Not all powers work effectively with auto-activation mode.
        """
        return self.add_command_arguments_pool(
            CommandGroupConstants.POWEXEC_AUTO, [_Power(power) for power in powers]
        )

    # endregion

    # region Generic Pool Methods
    def add_command_arguments_pool(
        self, command: str, *arg_lists: list
    ) -> "_CommandsTemplate":
        """
        Add a generic command pool with multiple argument list variations.

        Creates a command pool using the provided command and argument lists through
        _CommandFactory. This is the core method that handles all pool creation and
        enables complex command variations through cross-product generation.

        Args:
            command: The base slash command to use (e.g., "powexec_name", "emote")
            *arg_lists: Variable number of argument lists for cross-product generation

        Returns:
            Self for method chaining

        Example:
            >>> template = _CommandsTemplate()
            >>> # Single argument list
            >>> template.add_command_arguments_pool("emote", ["wave", "dance"])
            >>> # Multiple argument lists (cross-product)
            >>> template.add_command_arguments_pool("team", ["Hello", "Goodbye"], ["team", "broadcast"])

        Note:
            If no argument lists are provided, the method returns self without modification.
            TODO: Determine if this should raise an error or append the bare command.
            The pool name is generated using the command and argument list ID for uniqueness.
        """
        if not arg_lists:
            return self  # TODO: error or just append command? (2025/11/28)

        command_factory = _CommandFactory(command, *arg_lists)
        command_pool = Pool(f"{command}_{id(arg_lists)}", command_factory.build_all())

        self._commands.append(command_pool)
        return self

    # endregion

    # region Template Generation Methods
    def _build_one(self) -> CommandGroup:
        """Generate command group from current pool configuration."""
        return CommandGroup(super()._build_one())

    # endregion
