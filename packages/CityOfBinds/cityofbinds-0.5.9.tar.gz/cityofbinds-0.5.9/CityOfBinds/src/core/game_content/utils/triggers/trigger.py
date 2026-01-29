from ......utils.string_thing import _StringThing
from ....._configs.constants import GameConstants
from ....._configs.valid_input import TRIGGER_KEYS, TRIGGER_MODIFIERS


class _Trigger(_StringThing):
    """
    Represents a game input trigger consisting of an optional modifier and a key.

    A Trigger encapsulates key combinations used to activate binds in City of Heroes/Villains.
    It handles parsing, validation, and normalization of trigger strings in the format
    [MODIFIER+]KEY, such as "F1", "SHIFT+F1", or "SPACE".

    The trigger system supports all standard game keys and modifiers, providing validation
    against the game's accepted input combinations. Trigger strings are automatically
    normalized to uppercase for consistency.

    Key Features:
        - Automatic parsing of modifier+key combinations
        - Case-insensitive input with normalized output
        - Comprehensive validation against game-accepted keys/modifiers
        - Property-based access to individual components
        - String representation ready for bind file output

    Supported Modifiers:
        - SHIFT, CTRL, ALT (single modifiers only)

    Supported Keys:
        - Function keys (F1-F12), letters (A-Z), numbers (0-9)
        - Special keys (SPACE, TAB, ENTER, etc.)
        - Mouse buttons (LBUTTON, RBUTTON, MBUTTON, etc.)

    Example:
        >>> trigger = _Trigger("shift+f1")
        >>> trigger.modifier  # "SHIFT"
        >>> trigger.key       # "F1"
        >>> str(trigger)      # "SHIFT+F1"
        >>>
        >>> simple_trigger = _Trigger("w")
        >>> simple_trigger.key       # "W"
        >>> simple_trigger.modifier  # ""
        >>> str(simple_trigger)      # "W"

    Raises:
        ValueError: If trigger format is invalid or contains unsupported keys/modifiers
    """

    VALID_TRIGGER_KEYS = TRIGGER_KEYS
    VALID_TRIGGER_MODIFIERS = TRIGGER_MODIFIERS

    ### Initialization
    def __init__(self, trigger_string: str):
        """
        Initialize a new Trigger by parsing a trigger string.

        Parses a trigger string in the format [MODIFIER+]KEY and creates a validated
        trigger object. Only a single modifier is supported - multiple modifiers like
        Multiple modifiers are not supported. The string is automatically normalized
        (trimmed and uppercased) and validated against supported game keys and modifiers.

        Args:
            trigger_string: Key combination string to parse
                          Format: [MODIFIER+]KEY (e.g., "F1", "SHIFT+F1", "CTRL+Q")
                          Case-insensitive, will be normalized to uppercase
                          Only single modifiers supported

        Raises:
            ValueError: If trigger format is invalid, contains unsupported keys/modifiers,
                       has invalid structure, or attempts to use multiple modifiers

        Example:
            >>> # Simple key triggers
            >>> trigger1 = _Trigger("f1")        # Normalized to "F1"
            >>> trigger2 = _Trigger(" W ")       # Normalized to "W" (trimmed)
            >>>
            >>> # Single modifier triggers
            >>> trigger3 = _Trigger("shift+f1")     # Normalized to "SHIFT+F1"
            >>> trigger4 = _Trigger("CTRL+q")      # Normalized to "CTRL+Q"
            >>>
            >>> # Invalid triggers (will raise ValueError)
            >>> _Trigger("")              # Empty string
            >>> _Trigger("invalid+key")   # Unsupported key
            >>> _Trigger("CTRL+SHIFT+Q")  # Multiple modifiers not supported
            >>> _Trigger("f1+f2+f3")      # Too many parts

        Note:
            Validation occurs against VALID_TRIGGER_KEYS and VALID_TRIGGER_MODIFIERS
            constants, which contain all keys/modifiers accepted by the game.
        """
        self._modifier = None
        self._key = None

        self._throw_error_if_invalid_trigger_string(trigger_string)
        trigger_string = self._normalize_trigger_string(trigger_string)
        modifier, key = self._get_trigger_parts(trigger_string)
        self.modifier = modifier
        self.key = key

    # region Trigger Properties
    @property
    def modifier(self) -> str:
        """
        Get the modifier portion of the trigger (e.g., "SHIFT", "CTRL", "ALT").

        Returns:
            String containing the normalized single modifier, or empty string
            if no modifier is present. Always in uppercase.

        Example:
            >>> trigger = _Trigger("shift+f1")
            >>> trigger.modifier  # "SHIFT"
            >>>
            >>> trigger2 = _Trigger("f1")
            >>> trigger2.modifier  # ""
        """
        return self._modifier

    @modifier.setter
    def modifier(self, modifier: str):
        """Sets the trigger modifier after normalization and validation."""
        self._modifier = self._normalize_and_validate_modifier(modifier)

    @property
    def key(self) -> str:
        """
        Get the key portion of the trigger (e.g., "F1", "W", "SPACE").

        Returns:
            String containing the normalized key name, always in uppercase

        Example:
            >>> trigger = _Trigger("shift+f1")
            >>> trigger.key  # "F1"
            >>>
            >>> trigger2 = _Trigger(" w ")
            >>> trigger2.key  # "W"  (trimmed and uppercased)
        """
        return self._key

    @key.setter
    def key(self, key: str):
        """Sets the trigger key after normalization and validation."""
        self._key = self._normalize_and_validate_key(key)

    # endregion

    # region Trigger Methods
    def has_modifier(self) -> bool:
        """
        Check if the trigger has a modifier component.

        Returns:
            True if the trigger includes a modifier (e.g., SHIFT, CTRL), False otherwise

        Example:
            >>> trigger1 = _Trigger("F1")
            >>> trigger1.has_modifier()  # False
            >>>
            >>> trigger2 = _Trigger("SHIFT+F1")
            >>> trigger2.has_modifier()  # True
        """
        return bool(self._modifier)

    def clear_modifier(self):
        """
        Remove the modifier from the trigger, leaving only the key.

        After calling this method, the trigger will represent a simple key press
        without any modifier keys.

        Example:
            >>> trigger = _Trigger("SHIFT+F1")
            >>> str(trigger)        # "SHIFT+F1"
            >>> trigger.clear_modifier()
            >>> str(trigger)        # "F1"
            >>> trigger.has_modifier()  # False
        """
        self._modifier = ""

    def get_str(self) -> str:
        """Build the complete trigger string from parts."""
        return self._build_trigger_string()

    def _build_trigger_string(self) -> str:
        if self._modifier:
            return f"{self._modifier}{GameConstants.TRIGGER_DELIM}{self._key}"
        return self._key

    # endregion

    # region Helper Methods
    def _get_trigger_parts(self, trigger_string: str) -> tuple[str, str]:
        """Extract modifier and key from trigger string."""
        modifier = self._get_modifier_from_trigger_string(trigger_string)
        key = self._get_key_from_trigger_string(trigger_string)
        return modifier, key

    def _get_modifier_from_trigger_string(self, trigger_string: str) -> str:
        """Helper function to extract the modifier from a trigger string."""
        parts = trigger_string.split(GameConstants.TRIGGER_DELIM)
        return parts[0] if len(parts) == 2 else ""

    def _get_key_from_trigger_string(self, trigger_string: str) -> str:
        """Helper function to extract the key from a trigger string."""
        parts = trigger_string.split(GameConstants.TRIGGER_DELIM)
        return parts[-1]  # Last part is always the key

    def _normalize_and_validate_modifier(self, modifier: str) -> str:
        modifier = self._normalize_modifier(modifier)
        self._throw_error_if_invalid_modifier(modifier)
        return modifier

    def _normalize_and_validate_key(self, key: str) -> str:
        key = self._normalize_key(key)
        self._throw_error_if_invalid_key(key)
        return key

    def _normalize_trigger_string(self, trigger_string: str) -> str:
        return trigger_string.strip()

    def _normalize_modifier(self, modifier: str) -> str:
        return modifier.strip().upper() if modifier else ""

    def _normalize_key(self, key: str) -> str:
        return key.strip().upper()

    # endregion

    # region Error Checking Methods
    def _throw_error_if_invalid_trigger_string(self, trigger_string: str):
        # TODO: write trigger string validation better (2025/12/07)
        trigger_parts = trigger_string.split(GameConstants.TRIGGER_DELIM)
        if len(trigger_parts) > 2:
            raise ValueError(
                f"Invalid trigger format '{trigger_string}'. Trigger format must follow [MODIFIER+]<KEY>."
            )
        if len(trigger_parts) == 2 and (not trigger_parts[0] or not trigger_parts[1]):
            raise ValueError(
                f"Invalid trigger format '{trigger_string}'. Trigger format must follow [MODIFIER+]<KEY>."
            )

    def _throw_error_if_invalid_key(self, key: str):
        if not key:
            raise ValueError("Trigger key cannot be empty.")
        if " " in key:
            raise ValueError(
                f"Invalid trigger key '{key}'. Trigger key cannot contain spaces."
            )
        if key not in self.VALID_TRIGGER_KEYS:
            self._throw_invalid_key_error(key)

    def _throw_invalid_key_error(self, key: str):
        raise ValueError(
            f"Unknown trigger key '{key}'. Please see https://homecoming.wiki/wiki/List_of_Key_Names for list of valid trigger keys."
        )

    def _throw_error_if_invalid_modifier(self, modifier: str):
        if not modifier:
            return
        if " " in modifier:
            raise ValueError(
                f"Invalid trigger modifier '{modifier}'. Trigger modifier cannot contain spaces."
            )
        if modifier not in self.VALID_TRIGGER_MODIFIERS:
            raise ValueError(
                f"Unknown trigger modifier '{modifier}'. Please see https://homecoming.wiki/wiki/List_of_Key_Names for list of valid trigger modifiers."
            )

    # endregion

    # region Dunder Methods
    def __repr__(self):
        """Return string representation for debugging."""
        if self.modifier:
            return f"{self.__class__.__name__}(key='{self.key}', modifier='{self.modifier}')"
        else:
            return f"{self.__class__.__name__}(key='{self.key}')"

    # endregion
