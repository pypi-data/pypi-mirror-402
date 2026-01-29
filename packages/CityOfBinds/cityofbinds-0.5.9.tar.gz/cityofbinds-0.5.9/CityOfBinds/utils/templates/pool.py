import random
from enum import Enum

from .constants import TemplateConstants


class SelectionType(Enum):
    SEQUENTIAL = 0
    RANDOM = 1
    RANDOM_ORDER = 2


class Pool:
    DEFAULT_SELECT_BEHAVIOR = SelectionType.SEQUENTIAL
    DEFAULT_IS_FINITE = False
    DEFAULT_RANDOM_SEED = 0xDEADBEEF

    def __init__(
        self,
        name: str,
        items,
        select_behavior: SelectionType = DEFAULT_SELECT_BEHAVIOR,
        is_finite: bool = DEFAULT_IS_FINITE,
        random_seed: int = DEFAULT_RANDOM_SEED,
    ):
        self.name: str = name
        # Ensure items is always a list
        if isinstance(items, list):
            self.items: list = items
        else:
            self.items: list = [items]
        self.is_finite: bool = is_finite
        self._select_type: SelectionType = select_behavior
        self.random_seed: int = random_seed

        self._access_count = 0
        self._random_gen = random.Random(self.random_seed)
        self._random_items = self._new_random_order(self.items)

    @property
    def access_count(self) -> int:
        return self._access_count

    def pop(self):
        item = self.peek()
        if item is not None:
            self._pop_update()
        return item

    def peek(self):
        if self._select_type == SelectionType.RANDOM:
            self._random_gen.seed(self._access_count + self.random_seed)
            return self._random_gen.choice(self.items)

        if self.is_finite and self._access_count == len(self.items):
            return None

        if self._select_type == SelectionType.SEQUENTIAL:
            return self.items[self._access_count % len(self.items)]

        if self._select_type == SelectionType.RANDOM_ORDER:
            """creates a new random list whenever random list is exhausted"""
            return self._random_items[self._access_count % len(self.items)]

    def set_select_behavior(
        self, behavior: SelectionType
    ):  # TODO: do I really want this value to be updated? Does it cause weird behavior as is? (2025/11/27)
        self._select_type = behavior

    def _pop_update(self):
        self._access_count += 1
        if self._select_type == SelectionType.RANDOM_ORDER:
            if self._access_count % len(self.items) == 0:
                self._random_items = self._new_random_order(self.items)

    def _new_random_order(self, items: list) -> list:
        random_items = items.copy()
        self._random_gen.shuffle(random_items)
        return random_items

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, items={self.items}, select_behavior={self._select_type}, is_finite={self.is_finite}, random_seed={self.random_seed})"

    def __str__(self):
        return f"{TemplateConstants.ENCAPSULATION_LEFT}{self.name}{TemplateConstants.ENCAPSULATION_RIGHT}"

    def __len__(self):
        return len(self.items)
