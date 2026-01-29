from .....utils.string_thing import _StringThing


class _Power(_StringThing):
    ### Initialization
    def __init__(self, power_string: str):
        formatted_power_string = power_string.lower().strip()
        self._power: str = formatted_power_string

    def get_str(self) -> str:
        return self._power

    # region Dunder Methods
    def __repr__(self) -> str:
        return f"Power('{self._power}')"

    # endregion
