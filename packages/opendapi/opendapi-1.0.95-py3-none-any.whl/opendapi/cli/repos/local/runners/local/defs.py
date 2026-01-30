"""Defs for the local runner"""

from enum import Enum


class RCAType(Enum):
    """The type of RCA to perform"""

    CONSECUTIVE_COMMITS = "consecutive-commits"
    TERMINAL_COMMITS = "terminal-commits"
