from enum import IntEnum


class Gender(IntEnum):
    MEN = 1
    WOMEN = 2
    MIXED = 3


class Stroke(IntEnum):
    FREESTYLE = 1
    BACKSTROKE = 2
    BREASTSTROKE = 3
    FLY = 4
    MEDLEY = 5
    CUSTOM = 99


class Round(IntEnum):
    TIMED_FINAL = 1
    PRELIMS = 2
    SWIMOFF_PRELIM = 3
    SEMIFINAL = 6
    SWIMOFF_SEMIFINAL = 7
    FASTEST_HEATS = 8
    FINALS = 9
    MEDAL_CEREMONY = 10
    BREAK = 11
    TIME_TRIAL = 17
    SLOWER_HEATS = 99


class HeatStatus(IntEnum):
    NULL = 0
    ENTRIES = 1
    SEEDED = 2
    RUNNING = 3
    UNOFFICIAL = 4
    OFFICIAL = 5
