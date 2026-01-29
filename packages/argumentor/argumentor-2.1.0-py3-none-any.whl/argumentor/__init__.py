# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

"""Main argumentor package."""

from gettext import textdomain
from typing import Tuple, Dict, Iterable, Type
from .builder import Builder, Val
from .const import Flags
from .helper import Helper
from .parser import Parser

textdomain("argumentor")

__all__ = ("__version__", "Argumentor", "Flags")
__version__ = "2.1.0"


class Argumentor(Builder):
    """Argumentor object."""

    def get_help(self, *args, **kwargs) -> str:  # pragma: no cover
        """Generate help page for the command-line interface.

        Args:
            single_command: print only given command (use '' to print all commands)
            print_global_options: print global options (default: True)
            print_all_options: print ALL options (default: False)
            print_options_for_command: print options available with given command
            show_hidden: show hidden commands/options as well (default: hide them)

        Returns:
            a formatted help page
        """
        helper = Helper(self)
        return helper.format_help(*args, **kwargs)

    def register_command(
        self,
        command: str,
        *aliases: str,
        description: str = "",
        value_type: Type[Val] = bool,
        value_name: str = "",
        hide: bool = False,
    ) -> None:
        """Register command to the command-line interface.

        Args:
            command: the command to register (typically something like "foo")
            aliases: aliases to register (typically something like "f" or "bar")
            description: a short description of the command (for help page)
            value_type: the expected type for the value of this command
            value_name: the name of the value (to display on help page)
            hide: hide this command from help page (default: display on help page)

        Returns:
            None
        """
        # pylint: disable=R0913,R0917
        self.add_command(
            command,
            description=description,
            value_type=value_type,
            value_name=value_name,
            hide=hide,
        )
        for alias in aliases:
            self.add_command_alias(alias, command)

    def register_option(
        self,
        option: str,
        *aliases: str,
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
            aliases: aliases to register (typically something like "-f" or "--bar")
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
        self.add_option(
            option,
            command=command,
            description=description,
            value_type=value_type,
            default_value=default_value,
            value_name=value_name,
            flags=flags,
            hide=hide,
        )
        for alias in aliases:
            self.add_option_alias(alias, option, command=command)

    def parse(
        self, args: Iterable[str] | None = None
    ) -> Tuple[Dict, Dict]:  # pragma: no cover
        """Parse command-line arguments.

        Args:
            args: the command-line arguments to parse

        Raises:
            ParsingError: when user input contains error (i.e. unexpected argument,
                mandatory options omitted, etc.)

        Returns:
            two dicts, one containing the command and its value(s), the other one containing
            options and their value(s)
        """
        parser = Parser(self, args)
        return parser.parse()
