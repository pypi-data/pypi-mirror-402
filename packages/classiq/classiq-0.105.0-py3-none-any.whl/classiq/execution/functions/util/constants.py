from enum import auto, unique

from classiq.interface.enum_utils import StrEnum


@unique
class Verbosity(StrEnum):
    QUIET = auto()
    INFO = auto()
