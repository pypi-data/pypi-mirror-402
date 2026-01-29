from pathlib import Path
from typing import Union

from .....utils.types.str_path import StrPath
from ...._configs.constants import BindFileConstants, GameConstants
from ..binds.bind import Bind
from ..command_group.command_group import CommandGroup
from ..macros.macro import Macro
from .comments.comment import Comment

# Centralized list of supported content types
_BIND_FILE_CONTENT_TYPES = (Bind, Comment, Macro, CommandGroup)

# Type alias derived from the centralized list
BindFileContentType = Union[*_BIND_FILE_CONTENT_TYPES]


class BindFile:
    BIND_STUB = Bind(BindFileConstants.STUB_TRIGGER, [BindFileConstants.STUB_COMMAND])
    """
    Represents a game bind file containing a collection of Binds and Comments.

    A BindFile manages an ordered collection of bind commands and comments that can be
    written to .txt files for use in City of Heroes/Villains. It provides methods for
    content manipulation, validation, file I/O, and preview generation.

    The BindFile maintains the order of its contents, allowing for precise control over
    how binds and comments appear in the generated file output.

    Example:
        >>> bf = BindFile()
        >>> bf.add_bind(Bind("F1", ["say hello"]))
        >>> bf.add_comment(_Comment("Greeting binds"))
        >>> bf.write_to_file("my_binds.txt")

    Attributes:
        contents: Ordered list of Bind and Comment instances
    """

    def __init__(
        self,
        content_list: list[BindFileContentType] = None,
        supress_load_errors: bool = True,
    ):
        """
        Initialize a new BindFile with optional starting content.

        Args:
            content_list: Optional list of Bind and/or Comment instances to initialize with.
                         If None, creates an empty BindFile.
            supress_load_errors: Whether to suppress errors during loading of content

        Raises:
            TypeError: If content_list is not a list or contains invalid content types

        Example:
            >>> # Empty bind file
            >>> bf = BindFile()
            >>> # Pre-populated bind file
            >>> binds = [Bind("F1", ["say hello"]), Bind("F2", ["say goodbye"])]
            >>> bf = BindFile(binds)
        """
        self._contents = []
        self.contents = content_list if content_list is not None else []
        self.supress_load_errors = supress_load_errors

    # region Properties
    @property
    def contents(self) -> list[BindFileContentType]:
        """
        Get the ordered list of all content in the bind file.

        Returns:
            List containing all Bind and Comment instances in their current order

        Example:
            >>> bf = BindFile([Bind("F1", ["say hi"]), _Comment("test")])
            >>> len(bf.contents)  # 2
        """
        return self._contents

    @contents.setter
    def contents(self, content_list: list[BindFileContentType]):
        """
        Set the contents of the bind file, replacing all existing content.

        Args:
            content_list: List of Bind and/or Comment instances

        Raises:
            TypeError: If content_list is not a list or contains invalid types

        Example:
            >>> bf = BindFile()
            >>> bf.contents = [Bind("F1", ["say hello"])]
        """
        if content_list is not None:
            self._throw_error_on_invalid_content_list(content_list)
        self._contents = content_list

    @property
    def binds(self) -> list[Bind]:
        """
        Get all Bind instances from the contents, filtering out all other items.

        Returns:
            List of Bind instances in their current order
        """
        return self._get_content_type(Bind)

    @property
    def macros(self) -> list[Macro]:
        """
        Get all Macro instances from the contents, filtering out all other items.

        Returns:
            List of Macro instances in their current order
        """
        return self._get_content_type(Macro)

    @property
    def command_groups(self) -> list[CommandGroup]:
        """
        Get all CommandGroup instances from the contents, filtering out all other items.

        Returns:
            List of CommandGroup instances in their current order
        """
        return self._get_content_type(CommandGroup)

    def _get_content_type(self, content_type: type) -> list[BindFileContentType]:
        """Get all content items of a specific type."""
        return [
            content for content in self._contents if isinstance(content, content_type)
        ]

    # endregion

    # region Content Management Methods
    def _add_content(
        self, content: BindFileContentType, expected_type: type
    ) -> "BindFile":
        """Helper method to validate and add content to the bind file."""
        self._throw_error_on_invalid_content_type(
            expected_type=expected_type, content=content
        )
        self._contents.append(content)
        return self

    def add_content(self, content: BindFileContentType) -> "BindFile":
        """
        Add a content item (Bind, Comment, Macro, or CommandGroup) to the end of the bind file.

        Args:
            content: The content item to add

        Returns:
            Self for method chaining

        Raises:
            TypeError: If content is not a supported type
        """
        if not isinstance(content, _BIND_FILE_CONTENT_TYPES):
            raise TypeError(f"Expected BindFileContent, got {type(content).__name__}")
        self._contents.append(content)
        return self

    def add_bind(self, bind: Bind) -> "BindFile":
        """
        Add a Bind instance to the end of the bind file contents.

        Args:
            bind: The Bind instance to add

        Returns:
            Self for method chaining

        Raises:
            TypeError: If bind is not a Bind instance

        Example:
            >>> bf = BindFile()
            >>> bf.add_bind(Bind("F1", ["say hello"])).add_bind(Bind("F2", ["say goodbye"]))
            >>> len(bf.contents)  # 2
        """
        return self._add_content(bind, Bind)

    def add_comment(self, comment: Comment) -> "BindFile":
        """
        Add a Comment instance to the end of the bind file contents.

        Args:
            comment: The Comment instance to add

        Returns:
            Self for method chaining

        Raises:
            TypeError: If comment is not a Comment instance
        """
        return self._add_content(comment, Comment)

    def add_macro(self, macro: Macro) -> "BindFile":
        """
        Add a Macro instance to the end of the bind file contents.

        Args:
            macro: The Macro instance to add

        Returns:
            Self for method chaining

        Raises:
            TypeError: If macro is not a Macro instance
        """
        return self._add_content(macro, Macro)

    def add_command_group(self, command_group: CommandGroup) -> "BindFile":
        """
        Add a CommandGroup instance to the end of the bind file contents.

        Args:
            command_group: The CommandGroup instance to add

        Returns:
            Self for method chaining

        Raises:
            TypeError: If command_group is not a CommandGroup instance
        """
        return self._add_content(command_group, CommandGroup)

    def remove_bind(self, trigger: str) -> "BindFile":
        """
        Remove all Bind instances with the specified trigger from the bind file.

        Args:
            trigger: The trigger key of the Bind(s) to remove

        Returns:
            Self for method chaining

        Example:
            >>> bf = BindFile([Bind("F1", ["say hello"]), Bind("F2", ["say goodbye"])])
            >>> bf.remove_bind("F1")
            >>> len(bf.contents)  # 1
        """
        self._contents = [
            content
            for content in self._contents
            if not (isinstance(content, Bind) and content.trigger == trigger)
        ]
        return self

    def clear(self) -> "BindFile":
        """
        Remove all contents from the bind file.

        Returns:
            Self for method chaining

        Example:
            >>> bf = BindFile([Bind("F1", ["say hello"])])
            >>> bf.clear()
            >>> bf.is_empty()  # True
        """
        self._contents.clear()
        return self

    # endregion

    # region Query and Preview Methods
    def preview(self) -> str:
        """
        Generate a preview of the bind file content as it would appear when written to disk.

        Returns:
            String representation of all contents joined with newlines.
            Empty string if the bind file has no content.

        Example:
            >>> bf = BindFile([Bind("F1", ["say hello"]), _Comment("test comment")])
            >>> print(bf.preview())
            # F1 "say hello"
            # # test comment #
        """
        return self._build_file_contents()

    def is_empty(self) -> bool:
        """
        Check if the bind file contains any content.

        Returns:
            True if the bind file has no Binds or Comments, False otherwise

        Example:
            >>> bf = BindFile()
            >>> bf.is_empty()  # True
            >>> bf.add_bind(Bind("F1", ["say hello"]))
            >>> bf.is_empty()  # False
        """
        return len(self._contents) == 0

    # endregion

    # region File I/O Methods
    def write_to_file(self, file_path: StrPath):
        """
        Write the bind file contents to a disk file.

        Automatically adds .txt extension if not present and validates that the
        extension is .txt. Creates parent directories as needed. Validates all
        binds before writing.

        Args:
            file_path: Path where the bind file should be written (string or Path)

        Raises:
            ValueError: If file extension is not .txt or binds fail validation
            IOError: If file cannot be written

        Example:
            >>> bf = BindFile([Bind("F1", ["say hello"])])
            >>> bf.write_to_file("my_binds.txt")
            >>> bf.write_to_file("my_binds")  # Auto-adds .txt extension
        """
        file_path = Path(file_path)

        # Auto-add .txt extension if missing
        if not file_path.suffix:
            file_path = file_path.with_suffix(BindFileConstants.FILE_EXTENSION)
        elif file_path.suffix != BindFileConstants.FILE_EXTENSION:
            raise ValueError(
                f"File must have '{BindFileConstants.FILE_EXTENSION}' extension, got '{file_path.suffix}'"
            )

        # Validate before writing
        self.validate()

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self._build_file_contents())

    def write_to_directory(self, filename: str, directory: StrPath = ".") -> None:
        """
        Convenience method to write the bind file to a specific directory with a filename.

        Args:
            filename: Name of the file to create (extension will be auto-added if missing)
            directory: Directory path where the file should be created (defaults to current directory)

        Example:
            >>> bf = BindFile([Bind("F1", ["say hello"])])
            >>> bf.write_to_directory("my_binds", "/home/user/binds")
            >>> # Creates /home/user/binds/my_binds.txt
        """
        directory = Path(directory)
        full_path = directory / filename
        self.write_to_file(full_path)

    # endregion

    # region Validation Methods
    def validate(self) -> None:
        """
        Validate the entire BindFile for common issues.

        Calls the validate_binds() method to check all Bind instances for validity.

        Raises:
            ValueError: If any bind fails validation
        """
        self.validate_binds()

    def validate_binds(self):
        """
        Validate all Bind instances in the bind file.

        Calls the validate() method on each Bind instance, which checks for
        common issues like empty binds or binds that exceed length limits.

        Raises:
            ValueError: If any bind fails validation

        Note:
            Comments are not validated as they have no validation requirements.

        Example:
            >>> bf = BindFile([Bind("F1", [])])  # Empty bind
            >>> bf.validate_binds()  # Raises ValueError
        """
        for bind in self.binds:
            bind.validate()

    # endregion

    # region Private Helper Methods
    def _build_file_contents(self) -> str:
        """Build complete file contents as string by joining all content items."""
        if self.is_empty():
            return ""
        return "\n".join(self._bf_str_repr(content) for content in self._contents)

    def _bf_str_repr(self, content: BindFileContentType) -> str:
        """Get the string representation of the content for bind file publishing"""
        if isinstance(content, Macro):
            return self._add_execute_stub(content.get_str())
        if isinstance(content, CommandGroup):
            return self._add_execute_stub(content.get_str().strip('"'))
        return content.get_str()

    def _add_execute_stub(self, content_str: str) -> str:
        """Return the command with an execute stub to allow execution on bind file load"""
        stub = ""
        if self.supress_load_errors:
            stub = self.BIND_STUB.get_str()
        return GameConstants.COMMANDS_DELIM.join([stub, content_str])

    # endregion

    # region Validation and Error Handling
    def _throw_error_on_invalid_content_list(
        self, content_list: list[BindFileContentType]
    ):
        """Validate content_list is a proper list of valid content types."""
        if not isinstance(content_list, list):
            raise TypeError(
                "Contents must be a list of supported BindFileContent types"
            )
        for content in content_list:
            if not isinstance(content, _BIND_FILE_CONTENT_TYPES):
                raise TypeError(
                    f"All items in contents must be instances of supported types: {[t.__name__ for t in _BIND_FILE_CONTENT_TYPES]}"
                )

    def _throw_error_on_invalid_content_type(self, expected_type, content):
        """Validate content is of the expected type."""
        if not isinstance(content, expected_type):
            raise TypeError(
                f"Expected content of type {expected_type.__name__}, got {type(content).__name__}"
            )

    # endregion

    # region Magic Methods
    def __repr__(self):
        """Return developer-friendly string representation."""
        return f"BindFile(contents={self._contents})"

    # endregion
