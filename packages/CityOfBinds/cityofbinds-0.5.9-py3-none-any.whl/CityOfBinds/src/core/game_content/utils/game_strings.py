from abc import abstractmethod

from .....utils.string_thing import _StringThing
from ...._configs.constants import GameExecutionCommands


class _GenericGameString(_StringThing):

    @abstractmethod
    def game_str(self) -> str:
        """Return the game string representation of the object."""
        pass


class _CommandString(_GenericGameString):
    def game_str(self) -> str:
        """
        Return the game string representation that would be used to run this command in-game.

        The game string is the exact format required by City of Heroes to execute
        the command, including any necessary prefixes, formatting, or syntax.

        Returns:
            str: The command string as it would appear when executed in the game client.
        """
        return f"{GameExecutionCommands.EXECUTE_COMMAND}{self.get_str()}"


class _BindString(_GenericGameString):
    def game_str(self) -> str:
        """
        Return the game string representation of the bind.

        The game string is the exact string one would enter into the chat window
        to load the bind.

        Returns:
            str: The bind string as it would be entered in the chat window.
        """
        return f"{GameExecutionCommands.EXECUTE_BIND} {self.get_str()}"
