import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Protocol

from .file_path_generator import FilePathGenerator
from .types.str_path import StrPath


class FileGraphDefaults:
    FILE_GRAPH_KEY = "file"
    PARENT_FOLDER = "graph_files"
    PUBLISH_DIRECTORY = "."
    ABSOLUTE_PATH_LINKS = False
    ARCHIVE_FORMAT = "zip"
    PATH_KWARGS = {}
    FILE_PATH_OVERRIDE_KEY = "FILE_PATH_OVERRIDE"


class FileGraphProtocol(Protocol):
    def nodes(self) -> Iterator: ...
    def out_edges(self, node_id: int, data: bool = False) -> Iterator[tuple]: ...

    nodes: any


class _FileGraphPublisher(ABC):
    def __init__(
        self,
        use_abs_path_links: bool = FileGraphDefaults.ABSOLUTE_PATH_LINKS,
        file_graph_key: str = FileGraphDefaults.FILE_GRAPH_KEY,
        file_path_override_key: str = FileGraphDefaults.FILE_PATH_OVERRIDE_KEY,
        file_paths_kwargs: dict = FileGraphDefaults.PATH_KWARGS,
    ):
        self.file_paths = None
        self.node_to_paths_id = None
        self.use_abs_path_links = use_abs_path_links
        self._file_graph_key = file_graph_key
        self._file_path_override_key = file_path_override_key
        self._file_paths_kwargs = file_paths_kwargs or {}

    def publish_files(
        self,
        file_graph: FileGraphProtocol,
        directory: StrPath = FileGraphDefaults.PUBLISH_DIRECTORY,
        parent_folder: str = FileGraphDefaults.PARENT_FOLDER,
    ):
        self.node_to_paths_id = self._create_node_to_paths_id(file_graph)
        file_paths_count = self._get_file_paths_count(self.node_to_paths_id)
        self.file_paths = FilePathGenerator(
            file_count=file_paths_count,
            parent_folder_name=parent_folder,
            **self._file_paths_kwargs,
        )
        directory = Path(directory)
        self._link_files(file_graph, self.node_to_paths_id, directory, self.file_paths)
        self._post_link_files(
            file_graph, self.node_to_paths_id, directory, self.file_paths
        )
        self._write_files(file_graph, self.node_to_paths_id, directory, self.file_paths)

    def publish_to_archive(
        self,
        file_graph: FileGraphProtocol,
        archive_directory: StrPath = FileGraphDefaults.PUBLISH_DIRECTORY,
        parent_folder: str = FileGraphDefaults.PARENT_FOLDER,
        archive_format: str = FileGraphDefaults.ARCHIVE_FORMAT,
    ):
        """Publish files to a temporary directory, then zip it up."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Publish files to temporary directory
            self.publish_files(file_graph, temp_dir, parent_folder)

            # Create zip file path (zip name matches parent folder)
            archive_path = Path(archive_directory) / f"{parent_folder}"
            archive_path.parent.mkdir(parents=True, exist_ok=True)

            # Create zip from the temp directory root (includes parent_folder structure)
            shutil.make_archive(str(archive_path), archive_format, temp_dir)

    def _create_node_to_paths_id(self, file_graph: FileGraphProtocol) -> dict:
        node_to_paths_id = {}
        file_paths_count = 0
        for node_id in file_graph.nodes():
            if self._has_file_path_override(file_graph, node_id):
                override_path = file_graph.nodes[node_id][self._file_path_override_key]
                node_to_paths_id[node_id] = override_path
                continue
            node_to_paths_id[node_id] = file_paths_count
            file_paths_count += 1
        return node_to_paths_id

    def _get_file_paths_count(self, node_to_paths_id: dict) -> int:
        return sum(1 for value in node_to_paths_id.values() if isinstance(value, int))

    def _has_file_path_override(
        self, file_graph: FileGraphProtocol, node_id: int
    ) -> bool:
        return (
            self._file_path_override_key in file_graph.nodes[node_id]
            and file_graph.nodes[node_id][self._file_path_override_key]
        )

    def _link_files(
        self,
        file_graph: FileGraphProtocol,
        node_to_paths_id: dict,
        directory: Path,
        file_paths,
    ):
        for source_node_id in file_graph.nodes():
            source_file = file_graph.nodes[source_node_id][self._file_graph_key]
            source_file_path = file_paths[node_to_paths_id[source_node_id]]

            for _, target_node_id, edge_data in file_graph.out_edges(
                source_node_id, data=True
            ):
                target_file = file_graph.nodes[target_node_id][self._file_graph_key]
                target_file_path = file_paths[node_to_paths_id[target_node_id]]

                if self.use_abs_path_links:
                    source_file_path = directory / source_file_path
                    target_file_path = directory / target_file_path

                self._link_file(
                    source_file,
                    target_file,
                    source_file_path,
                    target_file_path,
                    edge_data,
                )

    def _write_files(
        self,
        file_graph: FileGraphProtocol,
        node_to_paths_id: dict,
        directory: Path,
        file_paths,
    ):
        for node_id in file_graph.nodes():
            file = file_graph.nodes[node_id][self._file_graph_key]
            file_path = directory / file_paths[node_to_paths_id[node_id]]
            self._write_file(file, file_path)

    def _post_link_files(
        self,
        file_graph: FileGraphProtocol,
        node_to_paths_id: dict,
        directory: Path,
        file_paths,
    ):
        pass

    @abstractmethod
    def _link_file(
        self,
        source_file,
        target_file,
        source_file_path: Path,
        target_file_path: Path,
        edge_data: dict,
    ):
        pass

    @abstractmethod
    def _write_file(self, file, path: Path):
        pass
