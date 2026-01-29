from ..._configs.constants import BFGConstants
from ...core.content_managers.graph.bind_file_graph import BindFileGraph
from .generic_bfs_fixture import _RandomOrder
from .rotating_move_bind import RotatingMoveBind


class RandomWalk(_RandomOrder, RotatingMoveBind):
    def __init__(
        self,
        forward_key: str = "W",
        left_key: str = "A",
        backward_key: str = "S",
        right_key: str = "D",
        jump_key: str = "SPACE",
        down_key: str = "X",
        exclude_forward: bool = False,
        exclude_left: bool = False,
        exclude_backward: bool = False,
        exclude_right: bool = False,
        exclude_jump: bool = False,
        exclude_down: bool = False,
        is_silent: bool = True,
        absolute_path_links: bool = False,
        random_factor: int = 1,
        delay: int = 0,
    ):
        RotatingMoveBind.__init__(
            self,
            forward_key=forward_key,
            left_key=left_key,
            backward_key=backward_key,
            right_key=right_key,
            jump_key=jump_key,
            down_key=down_key,
            exclude_forward=exclude_forward,
            exclude_left=exclude_left,
            exclude_backward=exclude_backward,
            exclude_right=exclude_right,
            exclude_jump=exclude_jump,
            exclude_down=exclude_down,
            is_silent=is_silent,
            absolute_path_links=absolute_path_links,
            loop_delay=0,
        )
        _RandomOrder.__init__(self, random_factor=random_factor)
        self.delay = delay

    def _connect_bind_file_graph(
        self, bfg: BindFileGraph, bind_file_indexes: list[int], load_conditions: dict
    ):
        bfg.make_k_regular(
            bind_file_indexes,
            k=len(self.movement_keys),
            load_conditions=load_conditions,
            delay=self.delay,
        )
        self._set_wasd_load_conditions(bfg, bind_file_indexes)

    def _set_wasd_load_conditions(
        self, bfg: BindFileGraph, bind_file_indexes: list[int]
    ):
        for file_index in bind_file_indexes:
            edges = list(bfg.edges(file_index))

            for (source, target), trigger in zip(edges, self.movement_keys):
                bfg.edges[source, target][BFGConstants.EDGE_DATA_KEY] = {
                    BFGConstants.EXCLUSIVE_LOADING_TRIGGERS_KEY: [trigger]
                }
