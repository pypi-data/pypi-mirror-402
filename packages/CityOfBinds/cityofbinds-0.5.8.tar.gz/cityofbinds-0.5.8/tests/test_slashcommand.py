import pytest

from CityOfBinds.src.core.game_content.utils.slash_command import _SlashCommand


class TestInitialization:
    # region Valid Initialization Tests
    def test_init_should_accept_command_only(self):
        # arrange
        command_string = "nop"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "nop"

    def test_init_should_accept_command_with_underscores(self):
        # arrange
        command_string = "bind_load"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "bindload"

    def test_init_should_accept_command_with_single_char_args(self):
        # arrange
        command_string = "unbind T"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "unbind T"

    def test_init_should_accept_command_with_args(self):
        # arrange
        command_string = "powexectoggleon sprint"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "powexectoggleon sprint"

    def test_init_should_accept_command_with_multiple_word_args(self):
        # arrange
        command_string = "powexecauto super speed"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "powexecauto super speed"

    def test_init_should_accept_command_with_prefix(self):
        # arrange
        command_string = "+forward"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "+forward"

    def test_init_should_accept_command_with_doulbe_prefix(self):
        # arrange
        command_string = "++forward"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "++forward"

    def test_init_should_accept_uppercase_command(self):
        # arrange
        command_string = "PETSAYALL hello world"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "petsayall hello world"

    def test_init_should_accept_command_args_of_any_case(self):
        # arrange
        command_string = "petsayall Hello WORLD"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "petsayall Hello WORLD"

    def test_init_should_accept_command_args_with_numbers(self):
        # arrange
        command_string = "petsayall H3LL0 W0R1D"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "petsayall H3LL0 W0R1D"

    def test_init_should_accept_command_args_with_special_characters(self):
        # arrange
        command_string = "petsayall Hello_World!"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "petsayall Hello_World!"

    def test_init_should_accept_command_args_with_multiple_spaces(self):
        # arrange
        command_string = "petsayall Hello     World"
        # act
        action = _SlashCommand(command_string)
        # assert
        assert str(action) == "petsayall Hello     World"

    # endregion

    # region Invalid Initialization Tests
    def test_init_should_throw_error_given_too_many_prefixes(self):
        # arrange
        command_string = "+++forward"
        # act
        with pytest.raises(ValueError) as excinfo:
            _SlashCommand(command_string)
        # assert
        assert "Unknown slash command" in str(excinfo.value)

    def test_init_should_throw_error_given_invalid_characters_in_command(self):
        # arrange
        command_string = "for!ward"
        # act
        with pytest.raises(ValueError) as excinfo:
            _SlashCommand(command_string)
        # assert
        assert "Unknown slash command" in str(excinfo.value)

    # endregion


class TestValidSlashCommandInitialization:
    action_under_test = _SlashCommand

    def test_init_should_set_command_string_given_valid_command_string(self):
        # arrange
        valid_command_string = "powexectoggleon dark nova"
        # act
        action = self.action_under_test(valid_command_string)
        # assert
        assert str(action) == "powexectoggleon dark nova"

    def test_init_should_set_command_given_valid_command_string(self):
        # arrange
        valid_command_string = "powexectoggleon dark nova"
        # act
        action = self.action_under_test(valid_command_string)
        # assert
        assert action.slash_command == "powexectoggleon"

    def test_init_should_set_args_given_valid_command_string(self):
        # arrange
        valid_command_string = "powexectoggleon dark nova"
        # act
        action = self.action_under_test(valid_command_string)
        # assert
        assert action.args == "dark nova"

    def test_init_should_set_command_string_given_uppercase_command(self):
        # arrange
        uppercase_command = "POWEXECTOGGLEON dark nova"
        # act
        action = self.action_under_test(uppercase_command)
        # assert
        assert str(action) == "powexectoggleon dark nova"

    def test_init_should_set_command_given_uppercase_command(self):
        # arrange
        uppercase_command = "POWEXECTOGGLEON dark nova"
        # act
        action = self.action_under_test(uppercase_command)
        # assert
        assert action.slash_command == "powexectoggleon"

    def test_init_should_maintain_args_case_given_uppercase_args(self):
        # arrange
        uppercase_command_string = "POWEXECTOGGLEON DARK NOVA"
        # act
        action = self.action_under_test(uppercase_command_string)
        # assert
        assert action.args == "DARK NOVA"

    def test_init_should_set_command_string_given_command_string_with_no_args(self):
        # arrange
        valid_command_string = "forward"
        # act
        action = self.action_under_test(valid_command_string)
        # assert
        assert str(action) == "forward"

    def test_init_should_set_command_given_command_string_with_no_args(self):
        # arrange
        valid_command_string = "forward"
        # act
        action = self.action_under_test(valid_command_string)
        # assert
        assert action.slash_command == "forward"

    def test_init_should_set_args_to_empty_string_given_command_string_with_no_args(
        self,
    ):
        # arrange
        valid_command_string = "forward"
        # act
        action = self.action_under_test(valid_command_string)
        # assert
        assert action.args == ""
