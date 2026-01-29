# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Module containing class used to build command-line help page."""

from typing import Iterable, Dict
from gettext import gettext as _
from .builder import Builder
from .exc import CommandNotFoundException


def sort_args(args: Iterable[str]) -> Iterable[str]:
    """Sort arguments by length, and then by alphabetical order.

    Args:
        args: an iterable containing the arguments to sort

    Returns:
        an interable containing the sorted arguments
    """
    args_by_length: Dict = {}
    for arg in args:
        if args_by_length.get(len(arg)):
            args_by_length[len(arg)].append(arg)
        else:
            args_by_length[len(arg)] = [arg]
    for length in sorted(list(args_by_length.keys())):
        yield from sorted(args_by_length[length])


class Helper:
    """Command-line help page generator."""

    def __init__(self, builder: Builder) -> None:
        """Initialize a command-line help page object.

        Args:
            builder: an instance of Builder()
        """
        self.builder = builder
        self.max_line_size = 0

    def format_options(self, command: str, show_hidden: bool = False) -> str:
        """Generate help section for options that are available with given command.

        Args:
            command: the command to get available options for (use '*' for global options)
            show_hidden: show hidden options as well (default: hide hidden options)

        Returns:
            a formatted help section
        """
        if list(self.builder.get_options_for_command(command)):
            usage_help = (
                "\n" + _("global options:") + "\n"
                if command == "*"
                else "\n" + _("options for {}:").format(command) + "\n"
            )
            for option in self.builder.get_options_for_command(command):
                if (
                    self.builder.is_hidden(option["option"], command)
                    and not show_hidden
                ):
                    continue
                aliases = list(
                    sort_args(
                        self.builder.get_aliases(
                            option["option"], command, include_hidden=show_hidden
                        )
                    )
                )
                this_len = len(", ".join(aliases)) + 2
                self.max_line_size = (
                    this_len if self.max_line_size < this_len else self.max_line_size
                )
                usage_help += (
                    "  " + ", ".join(aliases) + "\t - " + option["description"] + "\n"
                )
            return usage_help
        return ""

    def format_help(
        self,
        single_command: str = "",
        print_global_options: bool = True,
        print_all_options: bool = False,
        print_options_for_command: str = "",
        show_hidden: bool = False,
    ) -> str:
        """Generate help page for the Builder() object.

        Args:
            single_command: print only given command (use '' to print all commands)
            print_global_options: print global options (default: True)
            print_all_options: print ALL options (default: False)
            print_options_for_command: print options available with given command
            show_hidden: show hidden commands/options as well (default: hide them)

        Returns:
            a formatted help page
        """
        # pylint: disable=R0913,R0917,R0912
        usage_help = _("usage: {}").format(self.builder.bin_name)
        if single_command and not self.builder.commands.get(single_command):
            if not self.builder.command_aliases.get(single_command):
                raise CommandNotFoundException(
                    _("command not found: {}").format(single_command)
                )
            single_command = self.builder.command_aliases[single_command]
        if print_options_for_command and not self.builder.commands.get(
            print_options_for_command
        ):
            if not self.builder.command_aliases.get(print_options_for_command):
                raise CommandNotFoundException(
                    _("command not found: {}").format(print_options_for_command)
                )
            print_options_for_command = self.builder.command_aliases[
                print_options_for_command
            ]
        usage_help += (
            f" {single_command}" if single_command else " <" + _("command") + ">"
        )
        usage_help += " <" + _("options") + ">\n" if self.builder.options else "\n"
        self.max_line_size = 0
        if not single_command:
            usage_help += "\n" + _("commands:") + "\n" if self.builder.commands else ""
            for command in self.builder.commands.values():
                if self.builder.is_hidden(command["command"]) and not show_hidden:
                    continue
                aliases = list(
                    sort_args(
                        self.builder.get_aliases(
                            command["command"], include_hidden=show_hidden
                        )
                    )
                )
                this_len = len(", ".join(aliases)) + 2
                self.max_line_size = (
                    this_len if self.max_line_size < this_len else self.max_line_size
                )
                usage_help += (
                    "  " + ", ".join(aliases) + "\t - " + command["description"] + "\n"
                )
        else:
            usage_help += (
                "\n" + self.builder.commands[single_command]["description"] + "\n"
            )
        if print_all_options:
            commands = ["*"]
            for command in self.builder.commands:
                if list(self.builder.get_options_for_command(command)):
                    if self.builder.is_hidden(command) and not show_hidden:
                        # do not print options that are specific to hidden commands
                        continue
                    commands.append(command)
        elif print_options_for_command:
            commands = [print_options_for_command]
            if print_global_options:
                commands += ["*"]
        elif print_global_options:
            commands = ["*"]
        for command in commands:
            usage_help += self.format_options(command, show_hidden)
        usage_help = usage_help.expandtabs(self.max_line_size + 2)
        # remove trailing "\n" character
        usage_help = usage_help[0:-1]
        return usage_help
