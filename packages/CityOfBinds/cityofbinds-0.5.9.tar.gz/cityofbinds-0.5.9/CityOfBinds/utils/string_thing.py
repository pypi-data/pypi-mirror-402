from abc import ABC, abstractmethod


class _StringThing(ABC):
    # TODO: rename this to something that isn't str (2026/01/04)
    @abstractmethod
    def get_str(self) -> str:
        """Return the object's string representation."""
        pass

    def __eq__(self, other):
        return self.get_str() == str(other)

    def __str__(self):
        return self.get_str()
