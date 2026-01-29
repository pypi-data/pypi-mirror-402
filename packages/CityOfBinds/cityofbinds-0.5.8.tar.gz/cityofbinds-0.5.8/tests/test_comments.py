import pytest

from CityOfBinds import Comment, CommentBanner


class TestCommentInitialization:
    COMMENT_UNDER_TEST = Comment

    def test_init_should_set_internal_text_given_valid_comment_text(self):
        # arrange
        valid_comment_text = "This is a comment"

        # act
        comment = self.COMMENT_UNDER_TEST(comment_text=valid_comment_text)

        # assert
        assert comment._text == "This is a comment"

    def test_init_should_default_internal_alignment_given_no_alignment(self):
        # arrange

        # act
        comment = self.COMMENT_UNDER_TEST(comment_text="This is a comment")

        # assert
        assert comment._alignment == "left"

    def test_init_should_set_internal_alignment_given_valid_alignment(self):
        # arrange
        valid_alignment = "center"
        # act
        comment = self.COMMENT_UNDER_TEST(
            comment_text="This is a comment", alignment=valid_alignment
        )
        # assert
        assert comment._alignment == "center"

    def test_init_should_default_internal_minimum_width_given_no_minimum_width(self):
        # arrange

        # act
        comment = self.COMMENT_UNDER_TEST(comment_text="This is a comment")

        # assert
        assert comment._minimum_width == Comment.MINIMUM_COMMENT_WIDTH

    def test_init_should_set_internal_minimum_width_given_valid_minimum_width(self):
        # arrange
        valid_minimum_width = 30
        # act
        comment = self.COMMENT_UNDER_TEST(
            comment_text="This is a comment", minimum_comment_width=valid_minimum_width
        )
        # assert
        assert comment._minimum_width == 30


class TestCommentBannerInitialization:
    COMMENT_BANNER_UNDER_TEST = CommentBanner
    VALID_COMMENT_TEXT = "This is a comment"

    def test_init_should_set_internal_text_given_valid_comment_text(self):
        # arrange
        valid_comment_text = "This is a comment"

        # act
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(comment_text=valid_comment_text)

        # assert
        assert comment_banner._text == "This is a comment"

    def test_init_should_default_internal_border_style_given_no_border_style(self):
        # arrange

        # act
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT
        )

        # assert
        assert comment_banner._border_style == "-"

    def test_init_should_set_internal_border_style_given_valid_border_style(self):
        # arrange
        valid_border_style = "-"
        # act
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT, border_style=valid_border_style
        )
        # assert
        assert comment_banner._border_style == "-"


class TestCommentBannerCommentTextProperty:
    COMMENT_BANNER_UNDER_TEST = CommentBanner
    VALID_COMMENT_TEXT = "This is a comment"

    def test_text_getter_should_return_comment_text(self):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text="This is a comment"
        )

        # act
        text = comment_banner.text

        # assert
        assert text == "This is a comment"

    def test_text_setter_should_set_internal_text_given_new_valid_text(self):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT
        )
        new_valid_comment_text = "This is a new comment"

        # act
        comment_banner.text = new_valid_comment_text

        # assert
        assert comment_banner._text == "This is a new comment"

    def test_text_setter_should_sanitize_text_given_text_with_blank_lines_and_whitespace(
        self,
    ):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT
        )
        text_with_blank_lines_and_whitespace = (
            "\n  Hello  \n\nThis is a comment\n  \nEnd  \n"
        )

        # act
        comment_banner.text = text_with_blank_lines_and_whitespace

        # assert
        assert comment_banner.text == "Hello\nThis is a comment\nEnd"


class TestCommentBannerBorderStyleProperty:
    COMMENT_BANNER_UNDER_TEST = CommentBanner
    VALID_COMMENT_TEXT = "This is a comment"

    def test_border_style_getter_should_return_border_style(self):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT, border_style="="
        )

        # act
        border_style = comment_banner.border_style

        # assert
        assert border_style == "="

    def test_border_style_setter_should_set_new_border_style_given_new_valid_border_style(
        self,
    ):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT
        )
        new_valid_border_style = "*"

        # act
        comment_banner.border_style = new_valid_border_style

        # assert
        assert comment_banner._border_style == "*"

    def test_border_style_setter_should_raise_value_error_given_invalid_border_style(
        self,
    ):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=self.VALID_COMMENT_TEXT, border_style="-"
        )
        invalid_border_style = "/"

        # act
        with pytest.raises(ValueError) as excinfo:
            comment_banner.border_style = invalid_border_style

        # assert
        assert "Invalid border style '/'. Valid options are: " in str(excinfo.value)


class TestCommentBannerCommentBannerStringProperty:
    COMMENT_BANNER_UNDER_TEST = CommentBanner

    def test_comment_string_getter_should_return_properly_formatted_comment_banner_string_given_single_line_comment(
        self,
    ):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text="Hello", border_style="-"
        )
        expected_banner_string = "# ----- #\n" "# Hello #\n" "# ----- #"

        # act
        banner_string = comment_banner.comment_string

        # assert
        assert banner_string == expected_banner_string

    def test_comment_string_getter_should_return_properly_formatted_comment_banner_string_given_multi_line_comment(
        self,
    ):
        # arrange
        comment_text = "Hello\nThis is a longer line\nEnd"
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(
            comment_text=comment_text, border_style="="
        )
        expected_banner_string = (
            "# ===================== #\n"
            "# Hello                 #\n"
            "# This is a longer line #\n"
            "# End                   #\n"
            "# ===================== #"
        )

        # act
        banner_string = comment_banner.comment_string

        # assert
        assert banner_string == expected_banner_string

    def test_comment_string_getter_should_return_empty_string_given_empty_comment_text(
        self,
    ):
        # arrange
        comment_banner = self.COMMENT_BANNER_UNDER_TEST(comment_text="")

        # act
        banner_string = comment_banner.comment_string

        # assert
        assert banner_string == ""
