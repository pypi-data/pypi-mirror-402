from .trigger import _Trigger


class _TriggerEnjoyer:
    """Mixin class to provide trigger management and functionality."""

    def __init__(self, trigger: str):
        """Initialize the trigger enjoyer with a validated trigger."""
        self._trigger: _Trigger = None
        self._allowed_keys = self._get_allowed_keys()
        self._allowed_modifiers = self._get_allowed_modifiers()
        self.trigger = trigger

    @property
    def trigger(self) -> _Trigger:
        """
        Get the current trigger instance.

        Returns:
            _Trigger: The trigger object managing key and modifier combinations
                     Contains parsed and validated key/modifier information
        """
        return self._trigger

    @trigger.setter
    def trigger(self, value):
        """Set trigger, ensuring it is valid and allowed."""
        value_str = str(value)
        trigger = _Trigger(value_str)  # valid
        self._throw_error_if_trigger_not_allowed(trigger)  # allowed
        self._trigger = trigger

    @property
    def allowed_keys(self) -> tuple[str, ...]:
        """Get the tuple of allowed trigger keys."""
        return tuple(self._get_allowed_keys())

    @property
    def allowed_modifiers(self) -> tuple[str, ...]:
        """Get the tuple of allowed trigger modifiers."""
        return tuple(self._get_allowed_modifiers())

    def _get_allowed_keys(self) -> list[str]:
        """Helper method to get the list of allowed trigger keys."""
        return _Trigger.VALID_TRIGGER_KEYS

    def _get_allowed_modifiers(self) -> list[str]:
        """Helper method to get the list of allowed trigger modifiers."""
        return _Trigger.VALID_TRIGGER_MODIFIERS

    def _throw_error_if_trigger_not_allowed(self, trigger: str):
        """Validate that the trigger is allowed by checking type and keys."""
        if trigger.key not in self._allowed_keys:
            raise ValueError(
                f"Trigger key '{trigger.key}' not allowed. Allowed keys: {self._allowed_keys}"
            )
        if trigger.modifier and trigger.modifier not in self._allowed_modifiers:
            raise ValueError(
                f"Trigger modifier '{trigger.modifier}' not allowed. Allowed modifiers: {self._allowed_modifiers}"
            )
