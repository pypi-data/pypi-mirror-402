import pytest

from CityOfBinds.src.core.game_content.utils.triggers.trigger import _Trigger


@pytest.fixture(params=[_Trigger])
def TriggerUnderTest(request):
    return request.param


class TestInitialization:
    # region Valid Initialization Tests
    def test_init_should_accept_single_char_key_only(self, TriggerUnderTest):
        # arrange
        trigger_string = "W"
        # act
        trigger = TriggerUnderTest(trigger_string)
        # assert
        assert str(trigger) == "W"

    def test_init_should_accept_multi_char_key_only(self, TriggerUnderTest):
        # arrange
        trigger_string = "SPACE"
        # act
        trigger = TriggerUnderTest(trigger_string)
        # assert
        assert str(trigger) == "SPACE"

    def test_init_should_accept_single_char_key_with_modifier(self, TriggerUnderTest):
        # arrange
        trigger_string = "SHIFT+W"
        # act
        trigger = TriggerUnderTest(trigger_string)
        # assert
        assert str(trigger) == "SHIFT+W"

    def test_init_should_accept_multi_char_key_with_modifier(self, TriggerUnderTest):
        # arrange
        trigger_string = "SHIFT+SPACE"
        # act
        trigger = TriggerUnderTest(trigger_string)
        # assert
        assert str(trigger) == "SHIFT+SPACE"

    def test_init_should_accept_lowercase_trigger_string(self, TriggerUnderTest):
        # arrange
        trigger_string = "shift+w"
        # act
        trigger = TriggerUnderTest(trigger_string)
        # assert
        assert str(trigger) == "SHIFT+W"

    # endregion

    # region Invalid Initialization Tests
    def test_init_should_throw_error_given_empty_trigger_string(self, TriggerUnderTest):
        # arrange
        trigger_string = ""
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Trigger key cannot be empty." in str(excinfo.value)

    def test_init_should_throw_error_given_trigger_string_with_multiple_modifiers(
        self, TriggerUnderTest
    ):
        # arrange
        trigger_string = "CTRL+SHIFT+W"
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Invalid trigger format" in str(excinfo.value)

    def test_init_should_throw_error_given_trigger_string_with_empty_expected_modifier(
        self, TriggerUnderTest
    ):
        # arrange
        trigger_string = "+W"
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Invalid trigger format" in str(excinfo.value)

    def test_init_should_throw_error_given_trigger_string_with_empty_expected_key(
        self, TriggerUnderTest
    ):
        # arrange
        trigger_string = "SHIFT+"
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Invalid trigger format" in str(excinfo.value)

    def test_init_should_throw_error_given_trigger_string_with_multiple_trigger_delims(
        self, TriggerUnderTest
    ):
        # arrange
        trigger_string = "SHIFT++W"
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Invalid trigger format" in str(excinfo.value)

    def test_init_should_throw_error_given_trigger_string_with_invalid_key(
        self, TriggerUnderTest
    ):
        # arrange
        trigger_string = "WW"
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Unknown trigger key" in str(excinfo.value)

    def test_init_should_throw_error_given_trigger_string_with_invalid_modifier(
        self, TriggerUnderTest
    ):
        # arrange
        trigger_string = "CTRLL+W"
        # act
        with pytest.raises(ValueError) as excinfo:
            TriggerUnderTest(trigger_string)
        # assert
        assert "Unknown trigger modifier" in str(excinfo.value)

    # endregion


class TestKeyProperty:
    # region Getter Tests
    def test_key_getter_should_return_key(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+SPACE")
        # act
        key = trigger.key
        # assert
        assert key == "SPACE"

    # endregion

    # region Valid Setter Tests
    def test_key_setter_should_set_key(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_key = "SPACE"
        # act
        trigger.key = new_key
        # assert
        assert trigger.key == "SPACE"

    def test_key_setter_should_set_key_only(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_key = "SPACE"
        # act
        trigger.key = new_key
        # assert
        assert str(trigger) == "SHIFT+SPACE"

    def test_key_setter_should_set_capital_key_given_lowercase_key(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_key = "space"
        # act
        trigger.key = new_key
        # assert
        assert trigger.key == "SPACE"

    # endregion

    # region Invalid Setter Tests
    def test_key_setter_should_throw_error_given_empty_key(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_key = ""
        # act
        with pytest.raises(ValueError) as excinfo:
            trigger.key = new_key
        # assert
        assert "Trigger key cannot be empty." in str(excinfo.value)

    def test_key_setter_should_throw_error_given_key_with_spaces(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_key = "LEFT CLICK"
        # act
        with pytest.raises(ValueError) as excinfo:
            trigger.key = new_key
        # assert
        assert "Trigger key cannot contain spaces." in str(excinfo.value)

    def test_key_setter_should_throw_error_given_invalid_key(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_key = "WW"
        # act
        with pytest.raises(ValueError) as excinfo:
            trigger.key = new_key
        # assert
        assert "Unknown trigger key" in str(excinfo.value)

    # endregion


class TestModifierProperty:
    # region Getter Tests
    def test_modifier_getter_should_return_modifier(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+SPACE")
        # act
        modifier = trigger.modifier
        # assert
        assert modifier == "SHIFT"

    # endregion

    # region Valid Setter Tests
    def test_modifier_setter_should_set_modifier(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = "CTRL"
        # act
        trigger.modifier = new_modifier
        # assert
        assert trigger.modifier == "CTRL"

    def test_modifier_setter_should_set_modifier_only(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = "CTRL"
        # act
        trigger.modifier = new_modifier
        # assert
        assert str(trigger) == "CTRL+W"

    def test_modifier_setter_should_set_capital_modifier_given_lowercase_modifier(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = "ctrl"
        # act
        trigger.modifier = new_modifier
        # assert
        assert trigger.modifier == "CTRL"

    def test_modifier_setter_should_set_empty_modifier_given_empty_string(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = ""
        # act
        trigger.modifier = new_modifier
        # assert
        assert trigger.modifier == ""

    # endregion

    # region Invalid Setter Tests
    def test_modifier_setter_should_remove_delim_given_empty_string(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = ""
        # act
        trigger.modifier = new_modifier
        # assert
        assert str(trigger) == "W"

    def test_modifier_setter_should_throw_error_given_modifier_with_spaces(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = "LEFT SHIFT"
        # act
        with pytest.raises(ValueError) as excinfo:
            trigger.modifier = new_modifier
        # assert
        assert "Trigger modifier cannot contain spaces." in str(excinfo.value)

    def test_modifier_setter_should_throw_error_given_invalid_modifier(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        new_modifier = "CTRLL"
        # act
        with pytest.raises(ValueError) as excinfo:
            trigger.modifier = new_modifier
        # assert
        assert "Unknown trigger modifier" in str(excinfo.value)

    # endregion


class TestHasModifierMethod:
    # region Tests
    def test_has_modifier_should_return_true_given_trigger_with_modifier(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        # act
        has_modifier = trigger.has_modifier()
        # assert
        assert has_modifier is True

    def test_has_modifier_should_return_false_given_trigger_without_modifier(
        self, TriggerUnderTest
    ):
        # arrange
        trigger = TriggerUnderTest("W")
        # act
        has_modifier = trigger.has_modifier()
        # assert
        assert has_modifier is False

    # endregion


class TestClearModifierMethod:
    # region Tests
    def test_clear_modifier_should_remove_modifier_from_trigger(self, TriggerUnderTest):
        # arrange
        trigger = TriggerUnderTest("SHIFT+W")
        # act
        trigger.clear_modifier()
        # assert
        assert trigger.modifier == ""
        assert str(trigger) == "W"

    # endregion
