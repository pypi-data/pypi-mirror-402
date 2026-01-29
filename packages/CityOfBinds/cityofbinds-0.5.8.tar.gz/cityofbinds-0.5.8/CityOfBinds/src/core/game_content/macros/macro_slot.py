from ...._configs.constants import GameConstants, MacroCommands
from .macro import Macro


class MacroSlot(Macro):
    MACRO_COMMAND = MacroCommands.MACRO_SLOT

    def __init__(self, name: str, tray: int, slot: int, commands: list[str] = None):
        """
        Initialize a new Macro with a name and optional commands.

        Args:
            name: Name of the macro
            commands: List of slash command strings to include in the macro
        """
        super().__init__(name, commands)
        self._tray = None
        self._slot = None
        self.tray = tray
        self.slot = slot

    @property
    def tray(self) -> int:
        """Get the tray number of the macro slot."""
        return self._tray

    @tray.setter
    def tray(self, value: int):
        """Set the tray number of the macro slot."""
        self._throw_error_if_tray_out_of_bounds(value)
        self._tray = value

    @property
    def slot(self) -> int:
        """Get the slot number within the tray."""
        return self._slot

    @slot.setter
    def slot(self, value: int):
        """Set the slot number within the tray."""
        self._throw_error_if_slot_out_of_bounds(value)
        self._slot = value

    @property
    def absolute_slot(self) -> int:
        """Get the absolute slot number."""
        return self._calculate_absolute_slot(self.tray, self.slot)

    def _build_macro_string(self) -> str:
        return (
            f'{self.MACRO_COMMAND} {self.absolute_slot} "{self.name}" {self.commands}'
        )

    def _calculate_absolute_slot(self, tray: int, slot: int) -> int:
        """Calculate the absolute slot number based on tray and slot."""
        return (tray - 1) * GameConstants.SLOTS_PER_TRAY + (slot - 1)

    def _throw_error_if_tray_out_of_bounds(self, tray: int):
        """Raise error if tray number is out of valid range."""
        if not (1 <= tray <= GameConstants.TRAY_COUNT):
            raise ValueError(
                f"Tray number {tray} is out of bounds. Must be between 1 and {GameConstants.TRAY_COUNT}."
            )

    def _throw_error_if_slot_out_of_bounds(self, slot: int):
        """Raise error if slot number is out of valid range."""
        if not (1 <= slot <= GameConstants.SLOTS_PER_TRAY):
            raise ValueError(
                f"Slot number {slot} is out of bounds. Must be between 1 and {GameConstants.SLOTS_PER_TRAY}."
            )
