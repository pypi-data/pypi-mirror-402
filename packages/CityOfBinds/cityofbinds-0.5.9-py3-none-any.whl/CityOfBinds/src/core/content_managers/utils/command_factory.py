from .....utils.templates.pool import Pool
from .....utils.templates.templates import StringTemplate


class _CommandFactory(StringTemplate):
    def __init__(self, command: str, *arg_lists: list):
        self._command = command
        self._argument_pools = []

        for index, argument_list in enumerate(arg_lists):
            pool = Pool(f"argument_{index}", argument_list)
            self._argument_pools.append(pool)

        self._command_template = f"{self._command} {' '.join([str(argument_pool) for argument_pool in self._argument_pools])}"

        super().__init__(self._command_template, self._argument_pools)
