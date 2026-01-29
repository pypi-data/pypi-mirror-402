from .rotating_move_bind import RotatingMoveBind


class PersistentToggles(RotatingMoveBind):
    def __init__(
        self,
        toggle_powers: list[str],
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
        self._toggle_powers = toggle_powers
        for power in reversed(toggle_powers):
            self.move_bind_template.add_toggle_on_power([power])

    def publish_bind_files(self, parent_folder_name="", directory="."):
        non_priority_powers = []
        priority_powers = self._toggle_powers[::-1]
        while len(non_priority_powers) != len(self._toggle_powers):
            try:
                return super().publish_bind_files(parent_folder_name, directory)
            except ValueError as ve:
                non_priority_powers.append(priority_powers.pop())
                # TODO: write a clear command for bind template (2026/01/10)
                self.move_bind_template.template = []
                self.move_bind_template.add_toggle_on_power_pool(non_priority_powers)
                for priority_power in priority_powers:
                    self.move_bind_template.add_toggle_on_power([priority_power])
        return super().publish_bind_files(parent_folder_name, directory)
