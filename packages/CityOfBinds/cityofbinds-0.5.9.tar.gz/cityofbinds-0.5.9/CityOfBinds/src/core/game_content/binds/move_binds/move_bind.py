from ....._configs.constants import Directions
from ....._configs.defaults import DirectionKeys
from ...command_group.command_group import CommandGroup
from ...utils.triggers.trigger import _Trigger
from ..bind import Bind


class MoveBind(Bind):
    """
    Represents a game bind that maps a trigger (key + optional modifier) to directional movement
    plus zero or more commands.

    Example:
        >>> bind = MoveBind("W", ["powexectoggleon sprint", "powexecauto hasten"])
        >>> str(bind)  # 'W "+forward$$powexectoggleon sprint$$powexecauto hasten"'
    """

    def __init__(
        self,
        trigger: str,
        commands: list[str] = None,
        forward_key: str = DirectionKeys.FORWARD_KEY,
        left_key: str = DirectionKeys.LEFT_KEY,
        backward_key: str = DirectionKeys.BACKWARD_KEY,
        right_key: str = DirectionKeys.RIGHT_KEY,
        jump_key: str = DirectionKeys.UP_KEY,
        down_key: str = DirectionKeys.DOWN_KEY,
    ):
        """
        Initialize a new MoveBind with a trigger, optional commands, and movement key mappings.

        Args:
            trigger: Key and optional modifier string that must match one of the directional keys
            commands: List of slash command strings to execute after the movement command
            forward_key: Key to move forward (default: W)
            left_key: Key to move left (default: A)
            backward_key: Key to move backwards (default: S)
            right_key: Key to move right (default: D)
            jump_key: Key to jump/move upward (default: SPACE)
            down_key: Key to move downward (default: X)

        Raises:
            ValueError: If trigger key doesn't match any of the configured movement keys

        Example:
            >>> # Basic WASD movement with power activation
            >>> bind = MoveBind("W", ["powexectoggleon sprint"])
            >>> str(bind)  # 'W "+forward$$powexectoggleon sprint"'

            >>> # Custom key mapping for left-handed layout
            >>> bind = MoveBind("I", ["powexectoggleon super speed"], forward_key="I")
            >>> str(bind)  # 'I "+forward$$powexectoggleon super speed"'
        """
        self.key_to_direction_map = {
            _Trigger(forward_key).key: Directions.FORWARD,
            _Trigger(left_key).key: Directions.LEFT,
            _Trigger(backward_key).key: Directions.BACKWARD,
            _Trigger(right_key).key: Directions.RIGHT,
            _Trigger(jump_key).key: Directions.UP,
            _Trigger(down_key).key: Directions.DOWN,
        }
        super().__init__(trigger, commands)

    # region Override Methods
    def _build_bind_string(self) -> str:
        """Build WASD bind string with automatic movement command injection."""
        movement_command = CommandGroup().add_movement(
            self.key_to_direction_map[self.trigger.key]
        )
        # Combine movement with user commands (movement comes first)
        commands_with_movement = movement_command + self.commands
        return self._build_bind_string_from_components(
            self.trigger, commands_with_movement
        )

    # endregion

    def _get_allowed_keys(self) -> list[str]:
        return list(self.key_to_direction_map.keys())
