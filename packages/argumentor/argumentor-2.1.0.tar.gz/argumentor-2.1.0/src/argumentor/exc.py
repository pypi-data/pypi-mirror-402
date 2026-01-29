# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Module that contains exceptions raised by argumentor."""


class CommandExistsException(IOError):
    """Raised when trying to add an already existing command."""


class CommandNotFoundException(IOError):
    """Raised when trying to do something with an unexisting command."""


class OptionExistsException(IOError):
    """Raised when trying to add an already existing option."""


class OptionNotFoundException(IOError):
    """Raised when trying to do something with an unexisting option."""


class ParsingError(IOError):
    """Raised when the Argumentor.parse() method fails because of invalid user input."""
