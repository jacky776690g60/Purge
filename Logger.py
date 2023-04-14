from typing import *
from enum import Enum
from TermArtist import TermArtist
from functools import total_ordering

@total_ordering
class DebugLevel(Enum):
    INFO = 0
    WARN = 1
    DEBUG = 2
    ERROR = 3
    ALL = 4

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Logger():
    """
    Logger containing multiple log levels
    """

    def __init__(self, log_level: DebugLevel) -> None:
        self.debug_level = log_level

    def info(self, value: Any, start="", end="\n"):
        if self.debug_level >= DebugLevel.INFO:
            print(f"{TermArtist.RESET}{start}[INFO]{TermArtist.RESET}", value, end=end)

    def warn(self, value: Any, start="", end="\n"):
        if self.debug_level >= DebugLevel.WARN:
            print(f"{TermArtist.YELLOW}{start}[WARN]{TermArtist.RESET}", value, end=end)

    def debug(self, value: Any, start="", end="\n"):
        if self.debug_level >= DebugLevel.DEBUG:
            print(f"{TermArtist.DEBUG}{start}[DEBUG]{TermArtist.RESET}", value, end=end)

    def error(self, value: Any, start="", end="\n"):
        if self.debug_level >= DebugLevel.ERROR:
            print(f"{TermArtist.RED}{start}[ERROR]{TermArtist.RESET}", value, end=end)
