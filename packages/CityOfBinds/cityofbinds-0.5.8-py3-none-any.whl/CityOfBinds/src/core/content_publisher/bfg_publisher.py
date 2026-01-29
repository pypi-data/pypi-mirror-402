import copy
from pathlib import Path

from ....utils.file_graph_publisher import _FileGraphPublisher
from ....utils.types.str_path import StrPath
from ..._configs.constants import BFGConstants, BindFileConstants, SafeInstallValues
from ..content_managers.graph.bind_file_graph import BindFileGraph
from ..game_content.bind_file.bind_file import BindFile
from ..game_content.binds.bind import Bind
from ..game_content.command_group.command_group import CommandGroup
from ..game_content.macros.macro import Macro
from .safe_install import InstallFiles


class BFGPublisher(_FileGraphPublisher):
    """
    Publisher for Bind File Graph (BFG) systems with file linking and cross-referencing.

    BFGPublisher specializes in publishing collections of interconnected bind files that
    can reference and load each other through bind commands. It handles the complex task
    of linking bind files together with conditional trigger-based loading, silent/verbose
    file transitions, and key up press activation.

    The publisher processes bind file graphs where nodes contain BindFile objects and edges
    define linking conditions between files. It automatically injects "bind_load_file"
    commands into appropriate binds based on trigger conditions, enabling sophisticated
    bind file rotation and navigation systems.

    Key Features:
        - Conditional bind file linking based on trigger inclusion/exclusion
        - Silent vs verbose file loading modes
        - Key up press activation for quick triggers
        - Automatic file path resolution with proper extensions
        - Integration with file graph publishing infrastructure

    Publisher Behavior:
        - Source files get "bind_load_file" commands added to specified binds
        - Target files get key up press activation for designated quick triggers
        - Linking conditions control which binds receive loading commands
        - File paths automatically receive .txt extensions for game compatibility

    Attributes:
        is_silent: Controls whether file transitions use silent mode (no chat messages)

    Example:
        >>> publisher = BFGPublisher(is_silent=True)
        >>> # Publish a graph where combat.txt links to travel.txt on F1 press
        >>> graph = create_bind_file_graph()
        >>> publisher.publish(graph, "/path/to/output/")
    """

    def __init__(
        self,
        is_silent: bool = True,
        use_absolute_paths: bool = False,
    ):
        """
        Initialize a new BFGPublisher with specified linking behavior.

        Creates a publisher configured for bind file graph processing with control over
        file loading verbosity and path resolution. The publisher integrates with the
        file graph publishing infrastructure while providing BFG-specific functionality.

        Args:
            is_silent: Whether to use silent file loading (True) or show chat messages (False)
                      Silent mode prevents "Loading bind file..." messages in game chat
            use_absolute_paths: Whether to use absolute paths in bind_load_file commands
                               False uses relative paths for portability

        Example:
            >>> # Silent publisher with relative paths (default)
            >>> publisher = BFGPublisher()
            >>> # Verbose publisher with absolute paths
            >>> publisher = BFGPublisher(is_silent=False, use_absolute_paths=True)

        Note:
            Silent mode is typically preferred to avoid cluttering game chat with
            file loading messages during bind file transitions.
        """
        self.is_silent = is_silent
        bfg_path_kwargs = {"file_extension": BindFileConstants.FILE_EXTENSION}
        super().__init__(
            use_abs_path_links=use_absolute_paths,
            file_graph_key=BFGConstants.NODE_DATA_KEY,
            file_path_override_key=BFGConstants.FILE_PATH_OVERRIDE_KEY,
            file_paths_kwargs=bfg_path_kwargs,
        )

    def publish_files(
        self,
        file_graph: BindFileGraph,
        directory: StrPath = "",
        parent_folder: str = "",
    ):
        graph_copy = copy.deepcopy(file_graph)
        self._create_safe_install(graph_copy)
        super().publish_files(graph_copy, directory, parent_folder)

    def _create_safe_install(self, file_graph: BindFileGraph):
        ordered_files = self._create_ordered_files()
        (install_index, load_index, unload_index) = self._add_install_files_to_bfg(
            file_graph, ordered_files
        )
        self._connect_install_files(file_graph, install_index, load_index, unload_index)

    def _create_ordered_files(self) -> dict[str, BindFile]:
        # TODO: find better way to resolve ordering, maybe done in safe_install.py? (2026/01/04)
        install_files_generator = InstallFiles()
        install_files_dict = {}
        install_files_dict[SafeInstallValues.INSTALL_FILE_NAME] = (
            install_files_generator.create_install_file()
        )
        install_files_dict[SafeInstallValues.LOAD_FILE_NAME] = (
            install_files_generator.create_load_file()
        )
        install_files_dict[SafeInstallValues.UNLOAD_FILE_NAME] = (
            install_files_generator.create_unload_file()
        )
        return install_files_dict

    def _add_install_files_to_bfg(
        self, file_graph: BindFileGraph, install_files: dict[str, BindFile]
    ) -> tuple[int, int, int]:
        indexes = []
        for file_name, bind_file in install_files.items():
            file_graph.add_bind_file(bind_file=bind_file, file_path_override=file_name)
            file_index = file_graph.number_of_nodes() - 1
            indexes.append(file_index)
        return tuple(indexes)

    def _connect_install_files(
        self,
        file_graph: BindFileGraph,
        install_index: int,
        load_index: int,
        unload_index: int,
    ):
        file_graph.connect(
            install_index,
            load_index,
            load_conditions={
                BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY: [
                    SafeInstallValues.LOAD_MACRO_NAME
                ]
            },
        )
        file_graph.connect(
            install_index,
            unload_index,
            load_conditions={
                BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY: [
                    SafeInstallValues.UNLOAD_MACRO_NAME
                ]
            },
        )
        file_graph.add_backup_side_effect(install_index, install_index)
        file_graph.add_restore_side_effect(install_index, load_index)
        file_graph.add_restore_side_effect(load_index, 0)
        file_graph.add_restore_side_effect(unload_index, install_index)

    # region File Linking Methods
    def _link_file(
        self,
        source_bind_file: BindFile,
        target_bind_file: BindFile,
        source_file_path: Path,
        target_file_path: Path,
        edge_data: dict,
    ):
        """Link two bind files by updating source with load commands and target with key up settings."""
        load_conditions = edge_data[BFGConstants.EDGE_DATA_KEY]
        self._update_source_bind_file(
            source_bind_file,
            target_file_path,
            load_conditions,
        )
        self._update_target_bind_file(target_bind_file, load_conditions)

    def _update_source_bind_file(
        self,
        source_bind_file: BindFile,
        target_file_path: Path,
        load_conditions: dict[str, list[str]],
    ):
        """Add bind_load_file commands to qualifying binds in source file."""
        for bind in source_bind_file.binds:
            if self._should_link_bind(bind, load_conditions):
                self._link_bind(bind, target_file_path)

        for macro in source_bind_file.macros:
            if self._should_link_macro(macro, load_conditions):
                self._link_macro(macro, target_file_path)

    def _should_link_bind(
        self, bind: Bind, load_conditions: dict[str, list[str]]
    ) -> bool:
        """Check if bind qualifies for file linking based on inclusion/exclusion conditions."""
        if load_conditions is None:
            return True

        if BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY in load_conditions:
            return (
                bind.trigger
                in load_conditions[BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY]
            )

        if BFGConstants.NON_LOADING_TRIGGERS_KEY in load_conditions:
            return (
                bind.trigger
                not in load_conditions[BFGConstants.NON_LOADING_TRIGGERS_KEY]
            )

        return True

    def _link_bind(self, bind: Bind, target_file_path: Path):
        """Add silent or verbose bind_load_file command to bind."""
        if self.is_silent:
            bind.commands.add_bind_load_file_silent(target_file_path)
        else:
            bind.commands.add_bind_load_file(target_file_path)

    def _should_link_macro(
        self, macro: Macro, load_conditions: dict[str, list[str]]
    ) -> bool:
        """Check if macro qualifies for file linking based on inclusion/exclusion conditions."""
        if load_conditions is None:
            return True

        if BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY in load_conditions:
            return (
                macro.name
                in load_conditions[BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY]
            )

        if BFGConstants.NON_LOADING_TRIGGERS_KEY in load_conditions:
            return (
                macro.name not in load_conditions[BFGConstants.NON_LOADING_TRIGGERS_KEY]
            )

        return True

    def _link_macro(self, macro: Macro, target_file_path: Path):
        """Add silent or verbose bind_load_file command to macro."""
        if self.is_silent:
            macro.commands.add_bind_load_file_silent(target_file_path)
        else:
            macro.commands.add_bind_load_file(target_file_path)

    def _update_target_bind_file(
        self, target_bind_file: BindFile, load_conditions: dict[str, list[str]]
    ):
        """Enable key up press activation for specified quick triggers."""
        if (
            BFGConstants.QUICK_TRIGGER_KEY not in load_conditions
            or not load_conditions[BFGConstants.QUICK_TRIGGER_KEY]
        ):
            return

        for bind in target_bind_file.binds:
            if bind.trigger in load_conditions[BFGConstants.QUICK_TRIGGER_KEY]:
                bind.on_key_up = True

    # endregion

    # region File Output Methods
    def _write_file(self, bind_file: BindFile, bind_file_path: Path):
        """Write bind file to disk."""
        bind_file.write_to_file(bind_file_path)

    # endregion

    def _post_link_files(
        self, file_graph: BindFileGraph, node_to_paths_id, directory, file_paths
    ):
        for node_id in file_graph.nodes():
            self._resolve_side_effects(
                file_graph.get_bind_file(node_id),
                file_graph.nodes[node_id],
            )
            file_graph.get_bind_file(node_id).validate

    def _resolve_side_effects(
        self, source_bind_file: BindFile, source_node_attributes: dict
    ):
        """Add side effect commands to source bind file based on node attributes."""
        if BFGConstants.SIDE_EFFECTS_KEY not in source_node_attributes:
            return

        side_effects = source_node_attributes[BFGConstants.SIDE_EFFECTS_KEY]
        commands = CommandGroup()
        for side_effect in side_effects:
            command, target = side_effect
            target_file_path = self.file_paths[self.node_to_paths_id[target]]
            commands.add_command(f"{command} {target_file_path}")

        source_bind_file.add_command_group(commands)
