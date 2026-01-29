from ....._configs.defaults import DirectionKeys
from .move_bind import MoveBind


class WASDBind(MoveBind):
    def __init__(
        self,
        trigger: str,
        commands: list[str] = None,
    ):
        super().__init__(
            trigger,
            commands,
        )


class iWASDBind(MoveBind):
    def __init__(
        self,
        trigger: str,
        commands: list[str] = None,
    ):
        super().__init__(
            trigger,
            commands,
            forward_key=DirectionKeys.BACKWARD_KEY,
            left_key=DirectionKeys.RIGHT_KEY,
            backward_key=DirectionKeys.FORWARD_KEY,
            right_key=DirectionKeys.LEFT_KEY,
            jump_key=DirectionKeys.UP_KEY,
            down_key=DirectionKeys.DOWN_KEY,
        )
