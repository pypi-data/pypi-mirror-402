import copy
import random
from abc import ABC, abstractmethod

from ....utils.types.str_path import StrPath
from ..._configs.constants import BFGConstants
from ...core.content_managers.graph.bind_file_graph import BindFileGraph
from ...core.content_managers.templates.bind_file_template import BindFileTemplate
from ...core.content_managers.templates.bind_template import BindTemplate
from ...core.game_content.bind_file.bind_file import BindFile
from ..bind_file_system import BindFileSystem


class _GenericBFSFixture(ABC):
    def __init__(self, is_silent: bool = True, absolute_path_links: bool = False):
        self._base_bft: BindFileTemplate = BindFileTemplate()
        self.use_silent_loads = is_silent
        self.use_abs_path_loads = absolute_path_links

    @abstractmethod
    def _connect_bind_file_graph(
        self, bfg: BindFileGraph, bind_file_indexes: list[int]
    ):
        pass

    def publish_bind_files(
        self, parent_folder_name: str = "", directory: StrPath = "."
    ):
        bfs = self.get_bfs()
        bfs.publish_bind_files(parent_folder_name, directory)

    def archive_bind_files(
        self,
        parent_folder_name: str = "",
        archive_directory: StrPath = ".",
        archive_format: str = "zip",
    ):
        bfs = self.get_bfs()
        bfs.archive_bind_files(archive_directory, parent_folder_name, archive_format)

    def add_bind_template(
        self,
        bind_template: BindTemplate,
        loads_next_file: bool = True,
        execute_on_up_press: bool = False,
    ):
        self._base_bft.add_bind_template(
            bind_template, loads_next_file, execute_on_up_press
        )
        return self

    def add_non_loading_bind_template(
        self,
        bind_template: BindTemplate,
        execute_on_up_press: bool = False,
    ):
        self._base_bft.add_non_loading_bind_template(bind_template, execute_on_up_press)
        return self

    def add_exclusive_loading_bind_template(
        self,
        bind_template: BindTemplate,
        execute_on_up_press: bool = False,
    ):
        self._base_bft.add_exclusive_loading_bind_template(
            bind_template, execute_on_up_press
        )
        return self

    def get_bfs(self) -> BindFileSystem:
        indexed_bind_files = self._create_indexed_bind_files()
        load_conditions = self._get_load_conditions()
        # TODO: put "quick triggers" here, along with other params you think of (2026/01/09)
        load_parameters = self._get_load_parameters()
        bfs = self._create_bfs(indexed_bind_files, load_conditions)
        return bfs

    def _build_bind_files(self) -> list[BindFile]:
        return self._base_bft.build_all()

    def _create_indexed_bind_files(self) -> list[BindFile]:
        bind_files = self._build_bind_files()
        self._index_bind_files(bind_files)
        return bind_files

    def _index_bind_files(self, bind_files: list[BindFile]):
        pass

    def _get_load_conditions(self) -> dict:
        conditions = {}
        if self._base_bft.exclusive_load_triggers:
            conditions[BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY] = (
                self._base_bft.exclusive_load_triggers
            )
        if self._base_bft.non_load_triggers:
            conditions[BFGConstants.NON_LOADING_TRIGGERS_KEY] = (
                self._base_bft.non_load_triggers
            )
        if self._base_bft.quick_triggers:
            conditions[BFGConstants.QUICK_TRIGGER_KEY] = self._base_bft.quick_triggers
        return conditions

    def _get_load_parameters(self) -> dict:
        return {}

    def _create_bfs(
        self, indexed_bind_files: list[BindFile], load_conditions: dict
    ) -> BindFileSystem:
        bfs = BindFileSystem(self.use_silent_loads, self.use_abs_path_loads)
        self._add_bind_files_to_graph(bfs.bfg, indexed_bind_files)
        self._connect_bind_file_graph(
            bfs.bfg, range(len(indexed_bind_files)), load_conditions
        )
        return bfs

    def _add_bind_files_to_graph(self, bfg: BindFileGraph, bind_files: list[BindFile]):
        for bind_file in bind_files:
            bfg.add_bind_file(bind_file)


class _RandomOrder:
    def __init__(self, random_factor: int = 1):
        self.random_factor = random_factor

    def _index_bind_files(self, bind_files: list[BindFile]):
        original_files = bind_files[:]
        for _ in range(self.random_factor - 1):
            bind_files.extend(copy.deepcopy(original_files))

        # bind_files.extend(copy.deebind_files * (self.random_factor - 1))
        random.shuffle(bind_files)
