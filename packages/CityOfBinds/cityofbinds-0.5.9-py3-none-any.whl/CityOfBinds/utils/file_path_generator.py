import math
from functools import cache
from pathlib import Path

from .base_converter import BaseConverter
from .types.str_path import StrPath


class FilePathGenerator:
    DEFAULT_PARENT_FOLDER_NAME = ""
    DEFAULT_MAX_FILES_PER_FOLDER = 256
    DEFAULT_FILE_EXTENSION = ""
    DEFAULT_PADDING_BEHAVIOR = True

    """ Generates a folder/file path based off maximum files and max files per folder."""

    def __init__(
        self,
        file_count: int,
        parent_folder_name: StrPath = DEFAULT_PARENT_FOLDER_NAME,
        max_files_per_folder: int = DEFAULT_MAX_FILES_PER_FOLDER,
        file_extension: str = DEFAULT_FILE_EXTENSION,
        enable_padding: bool = DEFAULT_PADDING_BEHAVIOR,
        path_alphabet: str = None,
    ):
        self._file_count = file_count
        self._parent_folder = Path(parent_folder_name)
        self._max_files_per_folder = max_files_per_folder
        self._file_extension = self._normalize_extension(file_extension)
        self._enable_padding = enable_padding
        self._base_converter = (
            BaseConverter(path_alphabet) if path_alphabet else BaseConverter()
        )
        self._cached_paths = {}

        # region Helper Properties to Precompute
        self._depth = None
        self._capacity = None
        self._depth_capacities = None
        self._part_width = None
        self._root_width = None
        self._calculate_helper_properties()
        self._padding_char = self._base_converter.alphabet[0]

        # endregion

    # region Properties
    @property
    def folder_depth(self) -> int:
        """Public property to get the folder depth (excluding file level)."""
        return self._depth - 1

    @property
    def max_path_length(self) -> int:
        """Public property to get the maximum length of the entire file path."""
        return len(str(self.get_path(self._file_count - 1)))

    # endregion

    # region Path Generation Methods
    def get_path(self, file_index: int) -> Path:
        """Generate the folder/file path for a specific file index."""
        self._throw_error_if_index_out_of_range(file_index)

        return self._get_full_path(file_index)

    def get_override_path(self, relative_path: StrPath) -> Path:
        """Generate a full path using a provided relative path."""
        return self._parent_folder / Path(relative_path).with_suffix(
            self._file_extension
        )

    @cache
    def _get_full_path(self, file_index: int) -> Path:
        return self._parent_folder / self._get_relative_path(file_index).with_suffix(
            self._file_extension
        )

    def _get_relative_path(self, file_index: int) -> Path:
        path_parts = self._make_path_parts(file_index)
        self._pad_path_parts(path_parts)
        self._trim_root_path_part(path_parts)

        return Path(*path_parts)

    def _make_path_parts(self, file_index: int) -> list[str]:
        path_parts = []
        remaining_index = file_index

        for depth_capacity in self._depth_capacities:
            part_index, remaining_index = divmod(remaining_index, depth_capacity)
            path_parts.append(self._base_converter[part_index])

        return path_parts

    def _pad_path_parts(self, path_parts: list[str]):
        if self._enable_padding:
            for i in range(len(path_parts)):
                path_parts[i] = path_parts[i].rjust(
                    self._part_width, self._padding_char
                )

    def _trim_root_path_part(self, path_parts: list[str]):
        if self._depth > 1:
            path_parts[0] = path_parts[0][-self._root_width :]

    # endregion

    # region Helper Calculation Methods
    def _calculate_helper_properties(self):
        self._depth = self._calculate_depth(
            self._file_count, self._max_files_per_folder
        )
        self._capacity = self._calculate_capacity(
            self._max_files_per_folder, self._depth
        )
        self._depth_capacities = self._calculate_depth_capacities(
            self._depth, self._capacity, self._max_files_per_folder
        )
        self._part_width = self._calculate_part_width(
            self._file_count, self._max_files_per_folder
        )
        self._root_width = self._calculate_root_width(self._file_count, self._capacity)

    def _calculate_depth(self, file_count: int, max_files_per_folder: int) -> int:
        """Calculate how many levels of nesting are needed."""
        if file_count <= max_files_per_folder:
            return 1
        return math.ceil(math.log(file_count, max_files_per_folder))

    def _calculate_capacity(self, max_files_per_folder: int, depth: int) -> int:
        """Calculate the total capacity of files given the depth and max files per folder."""
        return max_files_per_folder ** (depth - 1)

    def _calculate_depth_capacities(
        self, depth: int, full_path_capacity: int, max_files_per_folder: int
    ) -> list[int]:
        """Calculate the capacities at each depth level."""
        depth_capacities = []
        capacity = full_path_capacity

        for _ in range(depth):
            depth_capacities.append(capacity)
            capacity //= max_files_per_folder

        return depth_capacities

    def _calculate_part_width(self, file_count: int, max_files_per_folder: int) -> int:
        if file_count == 0:
            return 1
        max_index = min(file_count, max_files_per_folder) - 1
        return len(self._base_converter[max_index])

    def _calculate_root_width(self, file_count: int, capacity: int) -> int:
        if file_count == 0:
            return 1
        num_root_folders = math.ceil(file_count / capacity)
        max_root_index = num_root_folders - 1
        return len(self._base_converter[max_root_index])

    # endregion

    # region Extension Handling Methods
    def _normalize_extension(self, extension: str) -> str:
        """Normalize file extension to always include leading dot."""
        if not extension:
            return ""
        return extension if extension.startswith(".") else f".{extension}"

    # endregion

    # region Error Checking Methods
    def _throw_error_if_index_out_of_range(self, file_index: int):
        if file_index < 0 or file_index >= self._file_count:
            raise IndexError(
                f"File index '{file_index}' out of range [0, {self._file_count-1}]"
            )

    # endregion

    # region Dunder Methods
    def __getitem__(self, file_id: int | StrPath) -> Path:
        # TODO: convert this to happy path try/except? (2026/01/04)
        if isinstance(file_id, int):
            return self.get_path(file_id)
        if isinstance(file_id, StrPath):
            return self.get_override_path(file_id)
        raise TypeError(f"file_id must be an int or StrPath, got {type(file_id)}")

    # endregion
