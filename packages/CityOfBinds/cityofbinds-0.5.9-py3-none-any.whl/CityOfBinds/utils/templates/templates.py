import math
import re
from abc import ABC, abstractmethod

from .constants import TemplateConstants
from .pool import Pool


class _Template(ABC):
    def __init__(self, template):
        self.template = template

    @property
    def pools(self) -> list[Pool]:
        return self._get_pools()

    @abstractmethod
    def _get_pools(self) -> list[Pool]:
        pass

    @abstractmethod
    def _build_one(self):
        pass

    @property
    def unique_count(self) -> int:
        return self._get_unique_count()

    def build(self, count: int = 1):
        if count == 1:
            return self._build_one()
        return [self._build_one() for _ in range(count)]

    def build_all(self):
        return self.build(self.unique_count)

    def build_sets(self, set_count: int):
        return self.build(set_count * self.unique_count)

    def _get_unique_count(self) -> int:
        pool_lengths = [len(pool) for pool in self.pools]
        return self._calculate_unique_count_from_lengths(pool_lengths)

    def _calculate_unique_count_from_lengths(self, lengths: list[int]) -> int:
        if not lengths:
            return 1
        return math.lcm(*lengths)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(template={self.template}, pools={self.pools})"
        )


class StringTemplate(_Template):
    def __init__(self, template: str, pools: list[Pool] = None):
        _Template.__init__(self, template)
        self.pool_dict: dict[str, Pool] = {}

        if pools is not None:
            self.add_pools(pools)

    def add_pool(
        self, pool: Pool
    ) -> (
        "StringTemplate"
    ):  # TODO: is there need to add pools post init? Maybe delete (2025/11/30)
        self.pool_dict[pool.name] = pool
        return self

    def add_pools(self, pools: list[Pool]) -> "StringTemplate":
        for pool in pools:
            self.add_pool(pool)
        return self

    def _get_pools(self) -> list[Pool]:
        return list(self.pool_dict.values())

    def _build_one(self) -> str:
        placeholder_pattern = self._build_placeholder_regex()

        def replace_placeholder(match):
            placeholder_name = match.group(1)
            pool = self.pool_dict[placeholder_name]
            item = pool.pop()
            return str(item) if item is not None else ""

        result_string = placeholder_pattern.sub(replace_placeholder, self.template)
        return result_string

    def _build_placeholder_regex(self):
        pool_names = [re.escape(pool_name) for pool_name in self.pool_dict.keys()]
        pool_alternation = "|".join(pool_names)
        left_encap = re.escape(TemplateConstants.ENCAPSULATION_LEFT)
        right_encap = re.escape(TemplateConstants.ENCAPSULATION_RIGHT)
        pattern = f"{left_encap}({pool_alternation}){right_encap}"
        return re.compile(pattern)


class ListTemplate(_Template):
    def __init__(self, template: list):
        _Template.__init__(self, template)

    def _get_pools(self) -> list[Pool]:
        pools = []
        for item in self.template:
            if isinstance(item, Pool):
                pools.append(item)
        return pools

    def _build_one(self) -> list:
        new_list = []
        for item in self.template:
            if isinstance(item, Pool):
                pool_item = item.pop()
                if pool_item is not None:
                    new_list.append(pool_item)
            else:
                new_list.append(item)
        return new_list
