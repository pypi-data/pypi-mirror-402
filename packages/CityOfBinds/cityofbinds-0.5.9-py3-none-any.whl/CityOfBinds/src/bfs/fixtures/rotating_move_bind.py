import copy

from ...core.content_managers.templates.bind_template import BindTemplate
from ...core.content_managers.utils.commands_template import (
    _CommandsTemplate,  # TODO: implement base wasd bind to use commandstemplate (2025/12/27)
)
from ...core.game_content.binds.move_binds.move_bind import MoveBind
from .rotating_bind import RotatingBind


class RotatingMoveBind(RotatingBind):
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
        loop_delay: int = 0,
    ):
        RotatingBind.__init__(
            self,
            is_silent=is_silent,
            absolute_path_links=absolute_path_links,
            loop_delay=loop_delay,
        )
        direction_keys = [
            forward_key,
            left_key,
            backward_key,
            right_key,
            jump_key,
            down_key,
        ]
        exclude_flags = [
            exclude_forward,
            exclude_left,
            exclude_backward,
            exclude_right,
            exclude_jump,
            exclude_down,
        ]
        self.movement_keys = [
            key for key, exclude in zip(direction_keys, exclude_flags) if not exclude
        ]
        # TODO: add kwags for support of other MoveBinds (2026/01/08)
        self.move_bind_template = BindTemplate(
            self.movement_keys[0],
            bind_type=MoveBind,
            forward_key=forward_key,
            left_key=left_key,
            backward_key=backward_key,
            right_key=right_key,
            jump_key=jump_key,
            down_key=down_key,
        )

    def _build_bind_files(self):
        self._append_wasd_binds()
        return super()._build_bind_files()

    def _append_wasd_binds(self):
        for direction in self.movement_keys:
            direction_template = copy.deepcopy(self.move_bind_template)
            direction_template.trigger = direction
            self.add_bind_template(direction_template)
