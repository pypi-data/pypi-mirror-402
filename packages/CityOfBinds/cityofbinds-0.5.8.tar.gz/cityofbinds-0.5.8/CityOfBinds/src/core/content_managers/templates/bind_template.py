from ...game_content.binds.bind import Bind
from ...game_content.utils.triggers.trigger_mixin import _TriggerEnjoyer
from ..utils.commands_template import _CommandsTemplate


class BindTemplate(_TriggerEnjoyer, _CommandsTemplate):
    """
    Template for generating individual bind objects with configurable commands.

    BindTemplate combines trigger management with command template functionality to
    create individual bind objects. It serves as a factory for generating bind
    instances with specific triggers and collections of slash commands.

    The template inherits from both _TriggerMixin (for trigger validation and management)
    and _CommandsTemplate (for command collection and generation), providing a complete
    solution for bind creation with dynamic command sequences.

    Key Features:
        - Trigger validation and storage via _TriggerMixin
        - Command collection and templating via _CommandsTemplate
        - Dynamic bind generation with _build_one()
        - Support for multiple bind variations through unique count calculation
        - Extensible architecture for specialized bind types

    Class Attributes:
        BIND_TYPE: The type of bind object to create (default: Bind)

    Inheritance Chain:
        BindTemplate -> _TriggerMixin (trigger management)
                    -> _CommandsTemplate (command collection)

    Example:
        >>> template = BindTemplate("F1")
        >>> template.add_power("Hasten")
        >>> template.add_emote("wave")
        >>> bind = template._build_one()
        >>> print(bind.trigger)  # "F1"
        >>> print(len(bind.commands))  # 2
    """

    def __init__(self, trigger: str, bind_type: type[Bind] = Bind, **bind_kwargs):
        """
        Initialize a new BindTemplate with the specified trigger.

        Creates a bind template that can generate bind objects with the given trigger
        and any commands added through the inherited command template methods.

        Args:
            trigger: The key or key combination that will activate the bind
                    (e.g., "F1", "CTRL+ALT+Q", "LBUTTON")

        Example:
            >>> template = BindTemplate("SHIFT+F5")
            >>> template.add_command("say Hello World!")
            >>> bind = template._build_one()
            >>> bind.trigger  # "SHIFT+F5"

        Note:
            Trigger validation is handled by the _TriggerMixin parent class.
            Invalid triggers will raise appropriate exceptions during initialization.
        """
        _TriggerEnjoyer.__init__(self, trigger)
        _CommandsTemplate.__init__(self)
        self.bind_type = bind_type
        self.bind_kwargs = bind_kwargs

    # region Template Generation Methods
    def _build_one(self) -> Bind:
        """Generate bind object with current trigger and commands."""
        return self.bind_type(self.trigger, super()._build_one(), **self.bind_kwargs)

    # endregion
