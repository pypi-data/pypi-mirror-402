from .generic_bfs_fixture import _RandomOrder
from .rotating_bind import RotatingBind


class RandomRotatingBind(RotatingBind, _RandomOrder):
    def __init__(
        self,
        random_factor: int = 10,
        is_silent: bool = True,
        absolute_path_links: bool = False,
        loop_delay: int = 0,
    ):
        RotatingBind.__init__(
            self,
            is_silent=is_silent,
            absolute_path_links=absolute_path_links,
            loop_delay=loop_delay,
        )
        _RandomOrder.__init__(self, random_factor=random_factor)
