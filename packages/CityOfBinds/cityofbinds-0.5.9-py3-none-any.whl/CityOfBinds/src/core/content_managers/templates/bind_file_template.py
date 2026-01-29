from typing import Self

from .....utils.templates.templates import ListTemplate
from ...game_content.bind_file.bind_file import BindFile


class BindFileTemplate(ListTemplate):
    """
    Template for generating rotating bind files with controlled bind file advancement.

    A BindFileTemplate manages collections of bind templates that generate bind files
    capable of rotating to the next bind file in a sequence. It provides sophisticated
    control over which binds receive the "load next bind file" command through rotation policies.

    The template supports advanced rotation patterns:
    - Exclusive advancement (only specific triggers advance)
    - Inclusive advancement (all triggers advance by default)
    - Selective exclusion (all except specific triggers advance)
    - Key up press activation for selected triggers

    Key Concepts:
        - **Rotation**: Process of loading the next bind file in a sequence
        - **Advancement**: Adding the command to load the next bind file
        - **Exclusive Mode**: When ON_THIS_TRIGGER is used, only those binds advance
        - **Inclusive Mode**: Default behavior where all binds advance

    Attributes:
        include_triggers: List of triggers that will exclusively advance to next bind file
        exclude_triggers: List of triggers that will NOT advance to next bind file
        quick_triggers: List of triggers that activate on key up press in addition to key down

    Example:
        >>> template = BindFileTemplate()
        >>> # Normal bind - advances by default
        >>> template.add_bind_template(combat_bind)
        >>> # Only F1 will advance (exclusive mode activated)
        >>> template.add_bind_template(f1_bind, .ON_THIS_TRIGGER)
        >>> # F2 won't advance due to exclusive mode from F1
        >>> template.add_bind_template(f2_bind)
    """

    def __init__(self):
        """
        Initialize a new BindFileTemplate with empty trigger management lists.

        Creates a new template for rotating bind files with no bind templates and
        initializes all trigger management lists (include, exclude, quick) to empty states.

        The include/exclude lists control which binds get the "load next bind file" command
        when the rotating bind file sequence is generated and linked together.

        Example:
            >>> template = BindFileTemplate()
            >>> len(template.include_triggers)  # 0 - no exclusive advancement triggers
            >>> len(template.exclude_triggers)  # 0 - no excluded triggers
            >>> len(template.quick_triggers)    # 0 - no key up press triggers
        """
        ListTemplate.__init__(self, [])
        self.exclusive_load_triggers = []
        self.exclusive_load_macros = []
        self.non_load_triggers = []
        self.non_load_macros = []
        self.quick_triggers = []  # Triggers that activate on key up press

    # region Bind Template Management Methods
    def add_bind_template(
        self,
        bind_template,
        loads_next_file: bool = True,
        execute_on_up_press: bool = False,
    ) -> Self:
        """
        Add a bind template with specified rotation policy and quick trigger settings.

        Incorporates a bind template into the rotating bind file with configurable behavior
        for bind file advancement. The rotation policy determines whether this bind will
        receive the "load next bind file" command when the sequence is linked together.

        Args:
            bind_template: The bind template to add (must have a 'trigger' attribute)
            rotation_policy: Controls bind file advancement behavior:
                           - DEFAULT: Will advance to next file (unless exclusive mode activated)
                           - ON_THIS_TRIGGER: Only this trigger advances (activates exclusive mode)
                           - NOT_ON_THIS_TRIGGER: This trigger will never advance
            trigger_on_up_press: Whether this trigger should also activate on key release

        Returns:
            Self for method chaining

        Rotation Policy Behavior:
            - If any bind uses ON_THIS_TRIGGER, exclusive mode activates
            - In exclusive mode, only ON_THIS_TRIGGER binds get advancement commands
            - Multiple binds can use ON_THIS_TRIGGER to create an inclusive list
            - NOT_ON_THIS_TRIGGER excludes specific triggers from advancement

        Example:
            >>> template = BindFileTemplate()
            >>> # Basic bind - will advance by default
            >>> template.add_bind_template(basic_bind)
            >>> # Exclusive bind - only F1 will advance (activates exclusive mode)
            >>> template.add_bind_template(f1_bind, .ON_THIS_TRIGGER)
            >>> # F2 won't advance due to exclusive mode
            >>> template.add_bind_template(f2_bind)
            >>> # Multiple exclusive triggers
            >>> template.add_bind_template(f3_bind, .ON_THIS_TRIGGER)  # F3 also advances
        """
        # Apply rotation policy to trigger management
        if not loads_next_file:
            self.non_load_triggers.append(bind_template.trigger)

        # Enable key up press activation if requested
        if execute_on_up_press:
            self.quick_triggers.append(bind_template.trigger)

        self.template.append(bind_template)
        return self

    def add_non_loading_bind_template(
        self,
        bind_template,
        execute_on_up_press: bool = False,
    ) -> Self:
        """
        Add a bind template that will NOT load the next bind file, with optional quick trigger.

        Incorporates a bind template into the rotating bind file that will never receive
        the "load next bind file" command when the sequence is linked together.
        This is useful for binds that should not affect the rotation sequence.

        Args:
            bind_template: The bind template to add (must have a 'trigger' attribute)
            trigger_on_up_press: Whether this trigger should also activate on key release
        Returns:
            Self for method chaining
        # Apply non-loading policy to trigger management
        """
        return self.add_bind_template(
            bind_template,
            loads_next_file=False,
            execute_on_up_press=execute_on_up_press,
        )

    def add_exclusive_loading_bind_template(
        self,
        bind_template,
        execute_on_up_press: bool = False,
    ) -> Self:
        self.exclusive_load_triggers.append(bind_template.trigger)
        return self.add_bind_template(
            bind_template,
            loads_next_file=True,
            execute_on_up_press=execute_on_up_press,
        )

    # endregion

    # region Template Generation Methods
    def _build_one(self) -> BindFile:
        """Generate single bind file by processing all bind templates."""
        bind_file = BindFile()
        for bind_template in self.template:
            bind_file.add_bind(bind_template._build_one())
        return bind_file

    def _get_unique_count(self) -> int:
        """Calculate LCM of all template lengths for parallel iteration."""
        content_lengths = [content.unique_count for content in self.template]
        return self._calculate_unique_count_from_lengths(content_lengths)

    # endregion
