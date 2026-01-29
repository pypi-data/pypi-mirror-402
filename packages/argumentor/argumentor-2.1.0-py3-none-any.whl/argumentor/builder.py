# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Module for building command-line interface."""

import sys
from typing import Type, Iterable, Dict, List
from gettext import gettext as _
from .const import Flags
from .exc import (
    CommandExistsException,
    CommandNotFoundException,
    OptionExistsException,
    OptionNotFoundException,
)

Val = list | str | int | bool


class Builder:
    """Command-line interface builder."""

    def __init__(self, bin_name: str = "") -> None:
        """Initialize a command-line interface builder object.

        Args:
            bin_name: the name of the executable

        Returns:
            None
        """
        self.bin_name = bin_name if bin_name else sys.argv[0]
        self.commands: Dict = {}
        self.command_aliases: Dict = {}
        self.options: Dict = {}
        self.option_aliases: Dict = {}
        self.hidden_commands: List[str] = []
        self.hidden_options: Dict[str, List[str]] = {}

    def add_command(
        self,
        command: str,
        description: str = "",
        value_type: Type[Val] = bool,
        value_name: str = "",
        hide: bool = False,
    ) -> None:
        """Register command to the command-line interface.

        Args:
            command: the command to register (typically something like "foo")
            description: a short description of the command (for help page)
            value_type: the expected type for the value of this command
            value_name: the name of the value (to display on help page)
            hide: hide this command from help page (default: display on help page)

        Returns:
            None
        """
        # pylint: disable=R0913,R0917
        if command == "*":
            raise CommandExistsException(
                _("command '*' is reserved, use something else")
            )
        if command in self.command_aliases:
            raise CommandExistsException(
                _("command already defined: {}").format(command)
            )
        if value_type not in list(Val.__args__):
            raise ValueError(
                _("unsupported type: {}. you should use str, int or bool").format(
                    value_type
                )
            )
        self.commands[command] = {
            "command": command,
            "description": description,
            "value_type": value_type,
            "value_name": value_name,
        }
        self.command_aliases[command] = command
        if hide:
            self.hidden_commands.append(command)

    def add_command_alias(self, alias: str, command: str, hide: bool = False) -> None:
        """Register alias to existing command.

        Args:
            alias: the alias to register (typically something like "bar")
            command: the command to alias (e.g. "foo")
            hide: hide this alias from help page (default: display on help page)

        Returns:
            None
        """
        if alias == "*":
            raise CommandExistsException(
                _("command '*' is reserved, use something else")
            )
        if alias in self.command_aliases:
            raise CommandExistsException(_("command already defined: {}").format(alias))
        if command not in self.command_aliases:
            raise CommandNotFoundException(_("command not found: {}").format(command))
        self.command_aliases[alias] = self.command_aliases[command]
        if hide:
            self.hidden_commands.append(alias)

    def add_option(
        self,
        option: str,
        command: str = "*",
        description: str = "",
        value_type: Type[Val] = bool,
        default_value: Val | None = None,
        value_name: str = "",
        flags: Flags | None = None,
        hide: bool = False,
    ) -> None:
        """Register option to the command-line interface.

        Args:
            option: the option to register (typically something like "--foo")
            command: the command this option applies to (for general option, use '*')
            description: a short description of the option (for help page)
            value_type: the expected type for the value of this option
            default_value: the default value of this option if unspecified by user
            value_name: the name of the value (to display on help page)
            flags: flags to apply to this option
            hide: hide this option from help page (default: display on help page)

        Returns:
            None
        """
        # pylint: disable=R0913,R0917
        if command != "*" and command not in self.command_aliases:
            raise CommandNotFoundException(_("command not found: {}").format(command))
        if self.option_aliases.get(option):
            if command == "*":
                raise OptionExistsException(
                    _(
                        "option already defined: {}, therefore unable to add global"
                    ).format(option)
                )
            if self.option_aliases[option].get(command):
                raise OptionExistsException(
                    _("option already defined: {} for command {}").format(
                        option, command
                    )
                )
            if self.option_aliases[option].get("*"):
                raise OptionExistsException(
                    _("global option already defined: {}").format(option)
                )
        if value_type not in list(Val.__args__):
            raise ValueError(
                _("unsupported type: {}. you should use str, int or bool").format(
                    value_type
                )
            )
        if default_value is not None and not isinstance(default_value, value_type):
            raise ValueError(
                _(
                    "default value should be of type specified in value_type"
                    "(in that case: {}, and not {})"
                ).format(value_type, type(default_value))
            )
        if not self.option_aliases.get(option):
            self.option_aliases[option] = {}
        if not self.options.get(option):
            self.options[option] = {}
        self.options[option][command] = {
            "option": option,
            "command": command,
            "description": description,
            "value_type": value_type,
            "default_value": default_value,
            "value_name": value_name,
            "flags": flags,
        }
        self.option_aliases[option][command] = option
        if hide:
            if self.hidden_options.get(option):  # pragma: no cover
                self.hidden_options[option].append(command)
            else:
                self.hidden_options[option] = [command]

    def add_option_alias(
        self, alias: str, option: str, command: str = "*", hide: bool = False
    ) -> None:
        """Register alias to existing option.

        Args:
            alias: the alias to register (typically something like "--bar")
            option: the option to alias (e.g. "--foo")
            command: the command the option applies to (for general option, use '*')
            hide: hide this alias from help page (default: display on help page)

        Returns:
            None
        """
        if command != "*" and command not in self.command_aliases:
            raise CommandNotFoundException(_("command not found: {}").format(command))
        if self.option_aliases.get(alias):
            if command == "*":
                raise OptionExistsException(
                    _(
                        "option already defined: {}, therefore unable to add global"
                    ).format(alias)
                )
            if self.option_aliases[alias].get(command):
                raise OptionExistsException(
                    _("option already defined: {} for command {}").format(
                        alias, command
                    )
                )
            if self.option_aliases[alias].get("*"):
                raise OptionExistsException(
                    _("global exception already defined: {}").format(alias)
                )
        if (
            self.option_aliases.get(option) is None
            or command not in self.option_aliases[option]
        ):
            if command == "*":
                raise OptionNotFoundException(
                    _("global option not found: {}").format(option)
                )
            raise OptionNotFoundException(
                _("option not found: {} for command {}").format(option, command)
            )
        if not self.option_aliases.get(alias):
            self.option_aliases[alias] = {}
        self.option_aliases[alias][command] = option
        if hide:
            if self.hidden_options.get(alias):
                self.hidden_options[alias].append(command)
            else:
                self.hidden_options[alias] = [command]

    def get_aliases(
        self, arg: str, command: str | None = None, include_hidden: bool = True
    ) -> Iterable[str]:
        """Get aliases of a given command or option.

        Args:
            arg: the command or option to get aliases for
            command: (when arg is an option) the command the option applies to
            include_hidden: include hidden aliases (default: True)

        Returns:
            An iterable containing the aliases
        """
        if command is None:
            if self.commands.get(arg):
                for alias, cmd in self.command_aliases.items():
                    if cmd == arg:
                        if alias not in self.hidden_commands or include_hidden:
                            yield alias
        elif self.options.get(arg) and self.options[arg].get(command):
            for alias, opts in self.option_aliases.items():
                if opts.get(command):
                    if opts[command] == arg:
                        if (
                            not (
                                self.hidden_options.get(alias)
                                and command in self.hidden_options[alias]
                            )
                            or include_hidden
                        ):
                            yield alias

    def get_options_for_command(self, command: str) -> Iterable[Dict]:
        """Get available options of given command.

        Args:
            command: the command to get available options for

        Returns:
            An iterable of options
        """
        for commands in self.options.values():
            if commands.get(command):
                yield commands[command]

    def is_hidden(self, alias: str, command: str | None = None) -> bool:
        """Determine whether given command/option (or any alias) should be hidden from help page.

        Args:
            alias: the command or option (or any alias) to check
            alias_command: (which alias is an option) the command the option applies to

        Returns:
            bool: True if argument should be hidden
        """
        if command is None and alias in self.hidden_commands:
            return True
        if self.hidden_options.get(alias) and command in self.hidden_options[alias]:
            return True
        return False

    def expects_argument(self, alias: str, command_alias: str | None = None) -> bool:
        """Determine whether a given command/option (or any alias) expects a non-boolean value.

        Args:
            alias: the command or option (or any alias) to check
            alias_command: (when alias is an option) the command the option applies to

        Returns:
            bool: True if argument expects a non-boolean value
        """
        if self.command_aliases.get(alias):
            return self.commands[self.command_aliases[alias]]["value_type"] != bool
        if self.option_aliases.get(alias):
            if command_alias:
                command = self.command_aliases.get(command_alias)
                if command and self.option_aliases[alias].get(command):
                    return (
                        self.options[self.option_aliases[alias][command]][command][
                            "value_type"
                        ]
                        != bool
                    )
            if self.option_aliases[alias].get("*"):
                return (
                    self.options[self.option_aliases[alias]["*"]]["*"]["value_type"]
                    != bool
                )
        return False
