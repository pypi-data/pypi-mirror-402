# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Module containing flags that can be applied to options."""

from enum import Flag, auto

__all__ = ("Flags",)


class Flags(Flag):
    """Flags that can be applied to options.

    REQUIRED will make the option mandatory.
    SPECIAL will prevent commands expecting a value from failing
        when given option is present.

    Notes:
        If command-line interface builder doesn't contain any command,
        SPECIAL will have no particular effect.
    """

    REQUIRED = auto()
    SPECIAL = auto()
