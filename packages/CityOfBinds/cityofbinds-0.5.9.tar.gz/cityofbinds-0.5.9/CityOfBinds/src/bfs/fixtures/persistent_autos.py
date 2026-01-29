from .rotating_move_bind import RotatingMoveBind


class PersistentAutos(RotatingMoveBind):
    def __init__(
        self,
        auto_powers: list[str],
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
        loop_delay: int = 0,
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
            loop_delay=loop_delay,
        )
        self.move_bind_template.add_auto_power_pool(auto_powers)
