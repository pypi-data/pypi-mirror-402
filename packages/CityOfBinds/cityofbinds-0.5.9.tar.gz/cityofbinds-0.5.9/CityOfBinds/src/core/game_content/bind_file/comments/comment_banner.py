from .comment import Comment


class CommentBanner(Comment):
    VALID_BORDER_STYLES = ["-", "=", "*", "~", "#"]
    DEFAULT_BORDER_STYLE = VALID_BORDER_STYLES[0]

    def __init__(
        self,
        comment_text: str,
        alignment: str = Comment.DEFAULT_ALIGNMENT,
        minimum_comment_width: int = Comment.MINIMUM_COMMENT_WIDTH,
        border_style: str = DEFAULT_BORDER_STYLE,
    ):
        self._border_style = None

        super().__init__(
            comment_text=comment_text,
            alignment=alignment,
            minimum_comment_width=minimum_comment_width,
        )

        self.border_style = border_style

    ### Properties
    @property
    def border_style(self) -> str:
        return self._border_style

    @border_style.setter
    def border_style(self, border_style: str):
        self._throw_error_on_invalid_border_style(border_style=border_style)
        self._border_style = border_style

    @property
    def line_count(self) -> int:
        return self.comment_string.count("\n") + 1 if self.comment_string else 0

    ### Helpers
    def _sanitize_comment_text(self, comment_text: str) -> str:
        ### remove any blank lines and trims leading/trailing whitespace for each line
        return "\n".join(
            [
                self._sanitize_comment_line(line)
                for line in comment_text.split("\n")
                if line.strip()
            ]
        )

    def _build_comment_string(self) -> str:
        longest_line_width = self._get_longest_line_width(comment_text=self.text)
        text_width = self._get_text_width(
            text_width=longest_line_width, minimum_width=self.minimum_width
        )
        return self._build_comment_banner_string(
            comment_text=self.text,
            alignment=self.alignment,
            text_width=text_width,
            border_style=self.border_style,
        )

    def _build_comment_banner_string(
        self, comment_text: str, alignment: str, text_width: int, border_style: str
    ) -> str:
        border = Comment(f"{border_style * text_width}").comment_string

        comment_lines = "\n".join(
            self._build_comment_line_string(line, alignment, text_width)
            for line in comment_text.split("\n")
        )

        return f"{border}\n{comment_lines}\n{border}"

    def _get_longest_line_width(self, comment_text: str) -> int:
        return (
            max(len(line) for line in comment_text.split("\n")) if comment_text else 0
        )

    ### Error Checking/Validation
    def _throw_error_on_invalid_comment(self, comment_text: str):
        pass  # Allow multi-line comments, so skip parent validation

    def _throw_error_on_invalid_border_style(self, border_style: str):
        if border_style not in self.VALID_BORDER_STYLES:
            raise ValueError(
                f"Invalid border style '{border_style}'. Valid options are: {', '.join(self.VALID_BORDER_STYLES)}"
            )
