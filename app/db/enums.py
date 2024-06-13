from enum import IntEnum, unique


@unique
class ActionType(IntEnum):
    test_finished = 1
