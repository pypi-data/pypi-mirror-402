from CityOfBinds.utils.base_converter import BaseConverter


class TestInitialization:
    # region Valid Initialization Tests
    def test_init_should_use_default_alphabet_when_no_alphabet_is_provided(self):
        # arrange
        # act
        indexer = BaseConverter()
        # assert
        assert indexer.alphabet == BaseConverter.DEFAULT_ALPHABET

    def test_init_should_set_alphabet_when_valid_alphabet_is_provided(self):
        # arrange
        custom_alphabet = "ABCDEF"
        # act
        indexer = BaseConverter(custom_alphabet)
        # assert
        assert indexer.alphabet == custom_alphabet

    # endregion


class TestAlphabetProperty:
    # region Alphabet Setter Tests
    def test_alphabet_setter_should_set_alphabet_when_valid_alphabet_is_provided(self):
        # arrange
        indexer = BaseConverter()
        new_alphabet = "XYZ"
        # act
        indexer.alphabet = new_alphabet
        # assert
        assert indexer.alphabet == new_alphabet

    def test_alphabet_setter_should_raise_value_error_when_empty_alphabet_is_provided(
        self,
    ):
        # arrange
        indexer = BaseConverter()
        empty_alphabet = ""
        # act / assert
        try:
            indexer.alphabet = empty_alphabet
            assert False, "Expected ValueError for empty alphabet"
        except ValueError as e:
            assert str(e) == "Alphabet cannot be empty."

    def test_alphabet_setter_should_raise_value_error_when_non_unique_characters_are_provided(
        self,
    ):
        # arrange
        indexer = BaseConverter()
        non_unique_alphabet = "AABC"
        # act / assert
        try:
            indexer.alphabet = non_unique_alphabet
            assert False, "Expected ValueError for non-unique characters"
        except ValueError as e:
            assert str(e) == "Alphabet characters must be unique."

    # endregion


class TestCustomBaseConverters:
    # region Custom Alphabet Tests
    def test_base_converter_with_binary_alphabet_should_convert_indices_correctly(self):
        # arrange
        binary_alphabet = "01"
        indexer = BaseConverter(binary_alphabet)
        test_cases = {
            0: "0",
            1: "1",
            2: "10",
            3: "11",
            4: "100",
            5: "101",
            10: "1010",
        }
        # act / assert
        for index, expected in test_cases.items():
            assert indexer[index] == expected

    def test_base_converter_with_custom_alphabet_should_convert_indices_correctly(self):
        # arrange
        custom_alphabet = "XYZ"
        indexer = BaseConverter(custom_alphabet)
        test_cases = {
            0: "X",
            1: "Y",
            2: "Z",
            3: "YX",
            4: "YY",
            5: "YZ",
            6: "ZX",
        }
        # act / assert
        for index, expected in test_cases.items():
            assert indexer[index] == expected

    # endregion
