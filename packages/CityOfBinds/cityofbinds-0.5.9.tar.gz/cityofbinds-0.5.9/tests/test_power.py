import pytest

from CityOfBinds.src.core.game_content.utils.power import _Power


class TestInitialization:
    # region Valid Initialization Tests

    def test_init_should_accept_single_word_power_string(self):
        # arrange
        power_string = "hasten"
        # act
        power = _Power(power_string)
        # assert
        assert str(power) == "hasten"

    def test_init_should_accept_multi_word_power_string(self):
        # arrange
        power_string = "super speed"
        # act
        power = _Power(power_string)
        # assert
        assert str(power) == "super speed"

    def test_init_should_accept_uppercase_power_string(self):
        # arrange
        power_string = "SUPER SPEED"
        # act
        power = _Power(power_string)
        # assert
        assert str(power) == "super speed"

    # endregion
