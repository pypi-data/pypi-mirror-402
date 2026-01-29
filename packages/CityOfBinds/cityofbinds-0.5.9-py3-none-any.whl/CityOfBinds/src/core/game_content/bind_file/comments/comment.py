from ......utils.string_thing import _StringThing


class Comment(_StringThing):
    DEFAULT_ALIGNMENT = "left"
    TEXT_ALIGNMENT_MAPPINGS = {
        "left": str.ljust,
        "center": str.center,
        "right": str.rjust,
    }
    LEFT_EDGE = "# "
    RIGHT_EDGE = " #"
    EDGES_LENGTH = len(LEFT_EDGE) + len(RIGHT_EDGE)
    MINIMUM_COMMENT_WIDTH = EDGES_LENGTH + 1  # At least one character of text

    def __init__(
        self,
        comment_text: str,
        alignment: str = DEFAULT_ALIGNMENT,
        minimum_comment_width: int = MINIMUM_COMMENT_WIDTH,
    ):
        self._text: str = None
        self._alignment = None
        self._minimum_width = None

        self.text = comment_text
        self.alignment = alignment
        self.minimum_width = minimum_comment_width

    ### Properties
    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._throw_error_on_invalid_comment(comment_text=text)
        sanitized_comment_text = self._sanitize_comment_text(comment_text=text)
        self._text = sanitized_comment_text

    @property
    def alignment(self) -> str:
        return self._alignment

    @alignment.setter
    def alignment(self, alignment: str):
        self._throw_error_on_invalid_alignment(alignment=alignment)
        self._alignment = alignment

    @property
    def minimum_width(self) -> int:
        return self._minimum_width

    @minimum_width.setter
    def minimum_width(self, minimum_width: int):
        self._throw_error_on_invalid_minimum_width(minimum_width=minimum_width)
        self._minimum_width = minimum_width

    @property
    def comment_string(self) -> str:
        if not self.text:
            return ""
        return self.get_str()

    ### Helpers
    def _sanitize_comment_text(self, comment_text: str) -> str:
        return self._sanitize_comment_line(comment_line=comment_text)

    def _sanitize_comment_line(self, comment_line: str) -> str:
        return comment_line.strip()

    def get_str(self) -> str:
        return self._build_comment_string()

    def _build_comment_string(self) -> str:
        text_width = self._get_text_width(
            text_width=len(self.text), minimum_width=self.minimum_width
        )
        return self._build_comment_line_string(
            comment_text=self.text, alignment=self.alignment, text_width=text_width
        )

    def _build_comment_line_string(
        self, comment_text: str, alignment: str, text_width: int
    ) -> str:
        alignment_function = self.TEXT_ALIGNMENT_MAPPINGS[alignment]
        return f"{self.LEFT_EDGE}{alignment_function(comment_text, text_width)}{self.RIGHT_EDGE}"

    def _get_text_width(self, text_width: int, minimum_width: int) -> int:
        return max(text_width, minimum_width - self.EDGES_LENGTH)

    ### Error Checking/Validation
    def _throw_error_on_invalid_comment(self, comment_text: str):
        self._throw_error_on_invalid_comment_line(comment_text=comment_text)

    def _throw_error_on_invalid_comment_line(self, comment_text: str):
        if "\n" in comment_text:
            raise ValueError("Comment line may not contain line breaks.")

    def _throw_error_on_invalid_minimum_width(self, minimum_width: int):
        if minimum_width < self.MINIMUM_COMMENT_WIDTH:
            raise ValueError(
                f"Minimum width must be at least {self.MINIMUM_COMMENT_WIDTH}."
            )

    def _throw_error_on_invalid_alignment(self, alignment: str):
        if alignment not in self.TEXT_ALIGNMENT_MAPPINGS:
            raise ValueError(
                f"Invalid text alignment '{alignment}'. Valid options are: {', '.join(self.TEXT_ALIGNMENT_MAPPINGS.keys())}"
            )
