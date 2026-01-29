# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Module for standardizing command-line arguments.

This module transforms input arguments to make the parsing easier.
Examples include:
    -ln2 -> -l -n 2
    --option='value' -> --option value
"""

import re
from typing import Iterable, Tuple
from .builder import Builder


class Standardizer:
    """Class used for standardizing arguments."""

    def __init__(self, builder: Builder) -> None:
        """Initialize the object.

        Args:
            builder: an instance of Builder()
        """
        self.builder = builder

    @staticmethod
    def unquote(string: str) -> str:
        """Remove leading and trailing single/double quotes from a string.

        Args:
            string: the string to modify

        Returns:
            the unquoted string
        """
        if (string[0] == "'" and string[-1] == "'") or (
            string[0] == '"' and string[-1] == '"'
        ):
            return string[1:-1]
        return string

    @staticmethod
    def get_prefix(arg: str) -> Tuple[str, str]:
        """Get the prefix of an argument.

        This method determines whether the argument begins with a dash or has no prefix.

        Args:
            arg: the argument

        Returns:
            the prefix, alongside the argument with its prefix removed
        """
        if len(arg) < 1:
            return "", ""
        if arg[0] == "-":
            if len(arg) > 1:
                return "-", arg[1:]
            return "-", ""
        return "", arg

    def standardize(self, args: Iterable[str]) -> Iterable[str]:
        """Standardize input command-line arguments.

        Examples include:
            -ln2 -> -l -n 2
            --option='value' -> --option value

        Args:
            args: the arguments to standardize

        Returns:
            an iterable containing the standardized arguments
        """
        # pylint: disable=R0912
        struct_args = []
        skip_all = False
        count = 0
        # if no command was defined, use option-only mode
        # that means the first argument won't be treated as a command
        local_aliases = (
            self.builder.option_aliases
            if len(self.builder.command_aliases) == 0
            else self.builder.command_aliases
        )
        for arg in args:
            local_aliases = self.builder.option_aliases if count > 0 else local_aliases
            # if standardization is disabled, simply append the argument
            # while this could have been combined with the two conditions below,
            # it is kept as a separated branch for unit testing coverage purposes
            if skip_all:
                struct_args.append(arg)
            # if argument is '--', do not standardize any argument from that point
            elif arg == "--":
                struct_args.append(arg)
                skip_all = True
            # if current argument is no longer the first one, we will treat every
            # next one as an option
            elif local_aliases.get(arg):
                # if argument is valid command/option, store it
                struct_args.append(arg)
            elif local_aliases.get(arg.split("=")[0]):
                # if argument is invalid but contains "=" symbol,
                # split it in half and store both ends
                split_arg = arg.split("=")
                struct_args.append(split_arg[0])
                if len(split_arg) > 1:
                    struct_args.append(self.unquote("=".join(split_arg[1:])))
            elif re.match(r"^-?[^\s=-]+$", arg):
                # if argument is invalid but looks like a combination of several
                # "short" arguments (cf. regex above), more complex things take place :/
                # first determine the prefix (i.e. some short options typically start
                # with the "-" prefix, while others don't use any prefix).
                prefix, arg = self.get_prefix(arg)
                index = 0
                for char in arg:
                    # now for every character in the argument, test it against valid
                    # arguments
                    if index == 0:
                        # if first character is not recognized as a valid argument,
                        # return the whole argument and proceed to the next argument
                        if not local_aliases.get(prefix + char):
                            # argument is not a combination of
                            # short commands and options
                            struct_args.append(prefix + arg)
                            break
                        # if first character is recognized as a valid argument,
                        # store it and proceed to the next character
                        struct_args.append(prefix + char)
                    else:
                        # if we can be here, it means that the first character
                        # (after '-', if any) was a valid argument
                        if self.builder.expects_argument(
                            struct_args[-1], prefix + arg[0]
                        ) and (self.builder.option_aliases.get(struct_args[-1])):
                            # if previous argument expects the next one to be its value,
                            # then we store what's left of the current argument and
                            # proceed to the next argument
                            struct_args.append(self.unquote(arg[index:]))
                            break
                        if self.builder.option_aliases.get(prefix + char):
                            struct_args.append(prefix + char)
                        elif self.builder.option_aliases.get("-" + char):
                            # this is required because we want the following to work:
                            # ./myprogram ab = ./myprogram a -b
                            # where a = command
                            # and -b  = option
                            struct_args.append("-" + char)
                        else:
                            # as soon as a character (with its prefix) is invalid, store
                            # what's left of the argument and proceed to the next one
                            struct_args.append(self.unquote(arg[index:]))
                            break
                    index += 1
            else:
                # if argument is not valid, we store it either way
                # this function isn't here to handle errors
                struct_args.append(arg)
            count += 1
        return struct_args
