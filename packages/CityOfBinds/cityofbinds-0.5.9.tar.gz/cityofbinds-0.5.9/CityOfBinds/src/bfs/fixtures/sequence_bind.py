from ...core.content_managers.graph.bind_file_graph import BindFileGraph
from .generic_bfs_fixture import _GenericBFSFixture


class SequenceBind(_GenericBFSFixture):
    def __init__(
        self,
        is_silent: bool = True,
        absolute_path_links: bool = False,
        delay: int = 0,
    ):
        _GenericBFSFixture.__init__(
            self, is_silent=is_silent, absolute_path_links=absolute_path_links
        )
        self.loop_delay = delay

    def _connect_bind_file_graph(
        self, bfg: BindFileGraph, bind_file_indexes: list[int], load_conditions: dict
    ):
        bfg.path(
            bind_file_indexes,
            load_conditions=load_conditions,
            delay=self.loop_delay,
        )
