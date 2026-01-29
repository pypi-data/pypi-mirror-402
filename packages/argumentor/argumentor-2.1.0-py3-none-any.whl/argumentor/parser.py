# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Module for parsing command-line arguments."""

import sys
from typing import Iterable, Dict, Type, Tuple, List
from gettext import gettext as _
from .const import Flags
from .builder import Builder
from .exc import ParsingError
from .std import Standardizer


class Parser:
    """Command-line argument parser."""

    # pylint: disable=R0902

    def __init__(self, builder: Builder, args: Iterable[str] | None = None) -> None:
        """Initialize the command-line argument parser.

        Args:
            builder: an instance of Builder()
            args: the command-line arguments to parse

        Returns:
            None
        """
        self.output_command: Dict = {}  # will hold passed command (if any)
        self.output_options: Dict = {}  # will hold passed options (if any)
        self.arguments: Dict = {}
        self.command_used: None = None
        self._special_option_used: List[bool] = []
        self.skip_all = False
        self.builder = builder
        _std = Standardizer(self.builder)
        if args is None:
            args = sys.argv[1:] if len(sys.argv) > 1 else []
        self.args = _std.standardize(args)

    @staticmethod
    def convert_value(
        value: str | int, expected_type: Type[list | str | int]
    ) -> str | int | None:
        """Convert input value to its expected type.

        Args:
            value: either a string or an int

        Returns:
            the converted value (None will be returned if conversion fails)

        """
        try:
            return int(value) if expected_type == int else value
        except ValueError:
            return None

    @property
    def special_option_used(self) -> bool:
        """Whether an option with the SPECIAL flag was used.

        Notes:
            this should be used only while parsing
        """
        return True in self._special_option_used

    @staticmethod
    def is_special_option(option: Dict) -> bool:
        """Determine wether given option has the SPECIAL flag applied to it.

        Args:
            option: the option declaration

        Returns:
            True if option has the SPECIAL flag
        """
        return bool(option.get("flags") and Flags.SPECIAL in option["flags"])

    def store_argument(self, arg_data: Dict, value: int | str | None = None) -> None:
        """Store user-passed argument, alongside its value, for later use.

        Notes:
            this function also takes care of assigning values to arguments
            and raising errors when an argument is unexpected.

        Args:
            arg_data: the command/option declaration
            value: the optional value that is assigned to the argument

        Raises:
            ParingError: when an argument is unexpected

        Returns:
            None
        """
        # pylint: disable=R0912
        if value == "--":
            self.skip_all = True
            return
        if self.arguments.get("expects") and (
            self.arguments["expects"].get("option") != arg_data.get("option")
            or self.arguments["expects"].get("command") != arg_data.get("command")
        ):
            # if a previous option expects a value, any new
            # argument isn't allowed to expect a value as long as the first
            # one isn't satisfied. if that happens, the operation will fail
            raise ParsingError(
                _("error: value expected after: {}").format(
                    self.arguments["expects"].get("option")
                )
            )
        if arg_data["value_type"] == bool:
            # if command/option expects a boolean value, then its mere presence
            # will set its value to True.
            if arg_data.get("option"):
                # here the argument is an option
                self.output_options[arg_data["option"]] = True
                self._special_option_used.append(self.is_special_option(arg_data))
            else:
                # here the argument is a command
                self.output_command[arg_data["command"]] = True
                self.command_used = arg_data["command"]
                self.arguments = {}
        elif value is None:
            # if command/option expects a non-boolean value (i.e. string, integer
            # or list), its value will be in a separate argument
            # for this reason, we need to temporarily store the information
            # that a command/option expects a given value, so that the parser
            # won't interpret the next argument as an invalid argument, but rather
            # as the value that was expected by the former argument
            if arg_data.get("option"):
                # if the argument that expects a value is an option
                self.arguments["expects"] = {
                    "command": arg_data.get("command"),
                    "option": arg_data.get("option"),
                }
            if arg_data["value_type"] == list or arg_data.get("option") is None:
                # if either a) the argument is a command or b) the expected value
                # is a list, we won't force the value to be passed as the next argument,
                # but we will instead allow any further invalid argument to be
                # interpreted as a potential value
                self.arguments["allows"] = {
                    "command": arg_data.get("command"),
                    "option": arg_data.get("option"),
                }
                self.command_used = arg_data["command"]
        else:
            # if a value is specified, it means that the parser is now attempting to store
            # an argument, alongside its value, e.g. :
            # ./program dostuff --verbosity 3 --keep-alive
            #                               ^ if the argument is --verbosity,
            #                                 then the parser is currently here
            # first we convert the value to the type that was expected
            # e.g. "1" will become 1 if expected type is integer, etc.
            converted_value = self.convert_value(value, arg_data["value_type"])
            if converted_value is None:
                # if type conversion failed, then fail
                raise ParsingError(
                    _("error: illegal value '{}' for argument: {}").format(
                        value, arg_data.get("option") or arg_data.get("command")
                    )
                )
            if arg_data.get("option"):
                # here the argument that required the value is an option
                if arg_data["value_type"] == list:
                    # here the required value is a list, so we will only append the value
                    if self.output_options.get(arg_data["option"]):
                        self.output_options[arg_data["option"]].append(converted_value)
                    else:
                        self.output_options[arg_data["option"]] = [converted_value]
                else:
                    # here the required value is not a list, so we will store it
                    self.output_options[arg_data["option"]] = converted_value
                # finally determine whether the option was a "special" option
                # and store that information
                self._special_option_used.append(self.is_special_option(arg_data))
            else:
                # here the argument that required the value is a command
                if arg_data["value_type"] == list:
                    # like before, we will append the value if the type is list
                    if self.output_command.get(arg_data["command"]):
                        self.output_command[arg_data["command"]].append(converted_value)
                    else:
                        self.output_command[arg_data["command"]] = [converted_value]
                else:
                    # and store it if the type is not list
                    self.output_command[arg_data["command"]] = converted_value
            if (
                (arg_data["value_type"] == list)
                and self.arguments.get("allows")
                and (
                    self.arguments["allows"].get("option") != arg_data.get("option")
                    or self.arguments["allows"].get("command")
                    != arg_data.get("command")
                )
            ):
                # finally if invalid argument were allowed to be treated as a value
                # for AN OPTION, but another option that also expects a list as
                # its value was specified since, then the parser won't be allowed
                # to treat invalid arguments as values of the former
                # this is only logical, since the parser would not be able to determine
                # whether values are for option 1 or option 2
                self.arguments = {}
            else:
                # finally we clean any expected value since it was already satisfied
                self.arguments["expects"] = None

    def _cleanup(self) -> None:
        """Clean parser memory.

        This should be used after/before each use.
        """
        self.output_options = {}
        self.output_command = {}
        self.arguments = {}
        self.skip_all = False

    def _parse(self) -> None:
        """Parse command-line arguments."""
        count = 0
        for arg in self.args:
            if count == 0 and len(self.builder.command_aliases) > 0:
                # if some commands are defined the first argument MUST be a command.
                # it will fail otherwise.
                if not self.builder.command_aliases.get(arg):
                    raise ParsingError(_("error: illegal command: {}").format(arg))
                # if it is a command, then store it
                cmd = self.builder.commands[self.builder.command_aliases.get(arg)]
                self.store_argument(cmd)
            elif self.arguments.get("expects"):
                # if previous argument expects value, current argument MUST be its value
                # it will fail otherwise.
                if self.arguments["expects"].get("option"):
                    # here the expecter is an option
                    expecter = self.builder.options[
                        self.arguments["expects"]["option"]
                    ][self.arguments["expects"]["command"]]
                    # store the expected value
                    self.store_argument(expecter, arg)
            elif self.skip_all or not self.builder.option_aliases.get(arg):
                # if last argument doesn't expect value and current argument isn't a
                # valid option, another argument MUST allow the argument to be invalid.
                # it will fail otherwise.
                if self.arguments.get("allows"):
                    # here a previous argument allows the argument to be invalid
                    # i.e. the argument that allows that can store multiple values
                    # so the parser will treat invalid arguments as values
                    # from that point
                    if self.arguments["allows"].get("option"):
                        # here the allower is an option
                        allower = self.builder.options[
                            self.arguments["allows"]["option"]
                        ][self.arguments["allows"]["command"]]
                    else:
                        # here the allower is a command
                        allower = self.builder.commands[
                            self.arguments["allows"]["command"]
                        ]
                        # if only one value is required by the command,
                        # future invalid values will fail from that point
                        if allower["value_type"] != list:
                            self.arguments["allows"] = {}
                    # store the invalid argument which is treated as a value
                    self.store_argument(allower, arg)
                else:
                    # if the invalid argument is not allowed to be treated as
                    # a value, fail and stop here
                    raise ParsingError(_("error: illegal option: {}").format(arg))
            else:
                # if argument is recognized as valid option, it MUST be either a global
                # option, or an option compatible with the command used (if any)
                # it cannot be a command, since commands are always the first argument
                if self.command_used and self.builder.option_aliases[arg].get(
                    self.command_used
                ):
                    # here the argument is an option compatible with the command used
                    # if no command was used, then it means that the option is a global
                    # option
                    opt = self.builder.options[
                        self.builder.option_aliases[arg][self.command_used]
                    ][self.command_used]
                elif self.builder.option_aliases[arg].get("*"):
                    # here the argument is a global option
                    # although this is redundant with the previous condition if no
                    # command was used, it is still required in case a command WAS
                    # used.
                    opt = self.builder.options[self.builder.option_aliases[arg]["*"]][
                        "*"
                    ]
                else:
                    # if option is neither global nor compatible with the command used,
                    # it will fail
                    raise ParsingError(_("error: illegal option: {}").format(arg))
                # store argument regardless of what it was, as long as the operation
                # didn't fail
                self.store_argument(opt)
            count += 1

    def _validate(self) -> None:
        """Perform final checks after parsing has succeeded.

        These checks include:
            - ensuring that all commands an options that expected a value do indeed have one
            - ensuring that required options were present
            - adding a default value for options that have one and that weren't specified
            - enforcing the SPECIAL flag in case any option with it was specified

        Raises:
            ParingError: in case any of the first two checks fails
        """
        if self.arguments.get("expects"):
            # if last argument expected a value but no argument was specified after it,
            # it will fail
            raise ParsingError(
                _("error: expected argument after: {}").format(
                    self.arguments["expects"]["option"]
                    if self.arguments["expects"].get("option")
                    else self.arguments["expects"]["command"]
                )
            )
        if (
            self.arguments.get("allows")
            and not self.output_command.get(self.arguments["allows"]["command"])
            and not self.output_options.get(self.arguments["allows"].get("option"))
        ):
            # if some argument expected at least one value but got none, it will fail
            if self.special_option_used:
                if not self.arguments["allows"].get("option"):
                    self.output_command[self.arguments["allows"]["command"]] = None
            else:
                raise ParsingError(
                    _("error: expected argument after: {}").format(
                        self.arguments["allows"]["option"]
                        if self.arguments["allows"].get("option")
                        else self.arguments["allows"]["command"]
                    )
                )
        for option_commands in self.builder.options.values():
            option = None
            if self.command_used and self.command_used in option_commands:
                option = option_commands[self.command_used]
            elif "*" in option_commands:
                option = option_commands["*"]
            if option is not None:
                if self.output_options.get(option["option"]) is None:
                    if (
                        option["flags"] is not None
                        and Flags.REQUIRED in option["flags"]
                        and not self.special_option_used
                    ):
                        raise ParsingError(
                            _("error: mandatory option was omitted: {}").format(
                                option["option"]
                            )
                        )
                    if option["default_value"] is not None:
                        self.output_options[option["option"]] = option["default_value"]

    def parse(self) -> Tuple[Dict, Dict]:
        """Parse command-line arguments.

        Raises:
            ParsingError: when user input contains error (i.e. unexpected argument,
                mandatory options omitted, etc.)

        Returns:
            two dicts, one containing the command and its value(s), the other one containing
            options and their value(s)
        """
        self._cleanup()
        self._parse()
        self._validate()
        return self.output_command, self.output_options
