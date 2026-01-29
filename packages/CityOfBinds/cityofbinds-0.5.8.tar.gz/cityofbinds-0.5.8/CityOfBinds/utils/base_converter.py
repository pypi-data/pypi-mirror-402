from functools import lru_cache


class BaseConverter:
    """Converts numerical indices to string representations using a configurable alphabet."""

    DEFAULT_ALPHABET = "0123456789ABCDEF"

    def __init__(self, alphabet: str = DEFAULT_ALPHABET):
        self._alphabet = None
        self.alphabet = alphabet
        self._cached_convert = lru_cache(maxsize=1024)(self._convert)

    # region Properties
    @property
    def alphabet(self) -> str:
        return self._alphabet

    @alphabet.setter
    def alphabet(self, value: str):
        self._throw_error_if_invalid_alphabet(value)
        self._alphabet = value

    @property
    def base(self) -> int:
        return len(self._alphabet)

    # endregion

    # region Convert Methods
    def convert(self, number: int, to_alphabet: str = None) -> str:
        self._validate_input(number, to_alphabet)
        return self._cached_convert(number, to_alphabet or self._alphabet)

    def _convert(self, number: int, to_alphabet: str) -> str:
        """Get the string representation of the given number."""
        if number == 0:
            return to_alphabet[0]

        digits = []
        while number:
            number, remainder = divmod(number, len(to_alphabet))
            digits.append(to_alphabet[remainder])
        digits.reverse()

        return "".join(digits)

    # endregion

    # region Error Checking Methods
    def _validate_input(self, number: int, alphabet: str = None):
        self._throw_error_if_number_is_negative(number)
        if alphabet is not None:
            self._throw_error_if_invalid_alphabet(alphabet)

    def _throw_error_if_invalid_alphabet(self, alphabet: str):
        self._throw_error_if_empty_alphabet(alphabet)
        self._throw_error_if_non_unique_alphabet_characters(alphabet)

    def _throw_error_if_empty_alphabet(self, alphabet: str):
        if not alphabet:
            raise ValueError("Alphabet cannot be empty.")

    def _throw_error_if_non_unique_alphabet_characters(self, alphabet: str):
        if len(set(alphabet)) != len(alphabet):
            raise ValueError("Alphabet characters must be unique.")

    def _throw_error_if_number_is_negative(self, number: int):
        if number < 0:
            raise ValueError("Cannot convert negative numbers.")

    # endregion

    # region Dunder Methods
    def __getitem__(self, number: int) -> str:
        return self.convert(number)

    # endregion
