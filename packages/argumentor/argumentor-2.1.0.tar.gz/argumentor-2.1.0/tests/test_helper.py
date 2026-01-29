# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

from unittest import TestCase
from argumentor.builder import Builder
from argumentor.helper import Helper, sort_args
from argumentor.exc import CommandNotFoundException


class TestSortArgs(TestCase):

    def test_sort(self) -> None:
        r = sort_args(["--verbose", "-v", "v", "--v", "-a"])
        self.assertListEqual(list(r), ["v", "-a", "-v", "--v", "--verbose"])


class TestFormatOptions(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()
        self.builder.add_command("cmd", description="cmd desc")
        self.builder.add_option("--opt1", description="opt1 desc")
        self.builder.add_option("--opt2", "cmd", description="opt2 desc")
        self.helper = Helper(self.builder)

    def test_global(self) -> None:
        r = self.helper.format_options("*")
        self.assertIn("--opt1", r)
        self.assertNotIn("--opt2", r)

    def test_cmd(self) -> None:
        r = self.helper.format_options("cmd")
        self.assertNotIn("--opt1", r)
        self.assertIn("--opt2", r)

    def test_cmd_not_found(self) -> None:
        # this will not raise an error
        # that's why it should never be called directly
        r = self.helper.format_options("invalid")
        self.assertNotIn("--opt1", r)
        self.assertNotIn("--opt2", r)

    def test_hidden(self) -> None:
        self.builder.add_option("--hidden", hide=True)
        r = self.helper.format_options("*")
        self.assertIn("--opt1", r)
        self.assertNotIn("--hidden", r)

    def test_hidden_show(self) -> None:
        self.builder.add_option("--hidden", hide=True)
        r = self.helper.format_options("*", show_hidden=True)
        self.assertIn("--opt1", r)
        self.assertIn("--hidden", r)

    def test_alias(self) -> None:
        self.builder.add_option_alias("--alias", "--opt1")
        r = self.helper.format_options("*")
        self.assertIn("--opt1", r)
        self.assertIn("--alias", r)

    def test_alias_hidden(self) -> None:
        self.builder.add_option_alias("--show", "--opt1")
        self.builder.add_option_alias("--hide", "--opt1", hide=True)
        self.builder.add_option_alias("--hide2", "--opt1", hide=True)
        r = self.helper.format_options("*")
        self.assertIn("--opt1", r)
        self.assertIn("--show", r)
        self.assertNotIn("--hide", r)
        self.assertNotIn("--hide2", r)

    def test_alias_hidden_show(self) -> None:
        self.builder.add_option_alias("--show", "--opt1")
        self.builder.add_option_alias("--hide", "--opt1", hide=True)
        self.builder.add_option_alias("--hide2", "--opt1", hide=True)
        r = self.helper.format_options("*", show_hidden=True)
        self.assertIn("--opt1", r)
        self.assertIn("--show", r)
        self.assertIn("--hide", r)
        self.assertIn("--hide2", r)


class TestFormatHelp(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()
        self.builder.add_command("cmd1", description="cmd1 desc")
        self.builder.add_command("cmd2", description="cmd2 desc")
        self.builder.add_command("cmd3", description="cmd3 desc")
        self.builder.add_option("--opt1", description="opt1 desc")
        self.builder.add_option("--opt2", "cmd2", description="opt2 desc")
        self.builder.add_option("--opt3", "cmd3", description="opt3 desc")
        self.builder.add_option("--opt4", "cmd3", description="opt4 desc")
        self.helper = Helper(self.builder)

    def test_single_cmd_not_found(self) -> None:
        self.assertRaises(
            CommandNotFoundException, self.helper.format_help, single_command="invalid"
        )

    def test_single_cmd(self) -> None:
        r = self.helper.format_help(single_command="cmd1")
        self.assertIn("cmd1", r)
        self.assertNotIn("cmd2", r)
        self.assertNotIn("cmd3", r)

    def test_single_cmd_by_alias(self) -> None:
        self.builder.add_command_alias("c1", "cmd1")
        r = self.helper.format_help(single_command="c1")
        self.assertIn("cmd1", r)
        self.assertNotIn("cmd2", r)
        self.assertNotIn("cmd3", r)

    def test_print_opts_for_cmd_not_found(self) -> None:
        self.assertRaises(
            CommandNotFoundException,
            self.helper.format_help,
            print_options_for_command="invalid",
        )

    def test_print_opts_for_cmd(self) -> None:
        r = self.helper.format_help(print_options_for_command="cmd2")
        self.assertIn(
            "--opt1", r
        )  # --opt1 is global and globals are printed by default
        self.assertIn("--opt2", r)
        self.assertNotIn("--opt3", r)
        self.assertNotIn("--opt4", r)

    def test_print_opts_for_cmd_by_alias(self) -> None:
        self.builder.add_command_alias("c2", "cmd2")
        r = self.helper.format_help(print_options_for_command="c2")
        self.assertIn(
            "--opt1", r
        )  # --opt1 is global and globals are printed by default
        self.assertIn("--opt2", r)
        self.assertNotIn("--opt3", r)
        self.assertNotIn("--opt4", r)

    def test_default(self) -> None:
        r = self.helper.format_help()
        self.assertIn("cmd1", r)
        self.assertIn("cmd2", r)
        self.assertIn("cmd3", r)
        self.assertIn("--opt1", r)
        self.assertNotIn("--opt2", r)
        self.assertNotIn("--opt3", r)
        self.assertNotIn("--opt4", r)

    def test_default_hidden(self) -> None:
        self.builder.add_command("hidden", hide=True)
        r = self.helper.format_help()
        self.assertIn("cmd1", r)
        self.assertNotIn("hidden", r)

    def test_default_hidden_show(self) -> None:
        self.builder.add_command("hidden", hide=True)
        r = self.helper.format_help(show_hidden=True)
        self.assertIn("cmd1", r)
        self.assertIn("hidden", r)

    def test_print_all_opts(self) -> None:
        r = self.helper.format_help(print_all_options=True)
        self.assertIn("cmd1", r)
        self.assertIn("cmd2", r)
        self.assertIn("cmd3", r)
        self.assertIn("--opt1", r)
        self.assertIn("--opt2", r)
        self.assertIn("--opt3", r)
        self.assertIn("--opt4", r)

    def test_print_all_opts_hidden(self) -> None:
        self.builder.add_command("hidden", hide=True)
        self.builder.add_option("--opt5", "hidden")
        r = self.helper.format_help(print_all_options=True)
        self.assertIn("cmd1", r)
        self.assertIn("cmd2", r)
        self.assertIn("cmd3", r)
        self.assertNotIn("hidden", r)
        self.assertIn("--opt1", r)
        self.assertIn("--opt2", r)
        self.assertIn("--opt3", r)
        self.assertIn("--opt4", r)
        self.assertNotIn("--opt5", r)

    def test_print_all_opts_hidden_show(self) -> None:
        self.builder.add_command("hidden", hide=True)
        self.builder.add_option("--opt5", "hidden")
        r = self.helper.format_help(print_all_options=True, show_hidden=True)
        self.assertIn("cmd1", r)
        self.assertIn("cmd2", r)
        self.assertIn("cmd3", r)
        self.assertIn("hidden", r)
        self.assertIn("--opt1", r)
        self.assertIn("--opt2", r)
        self.assertIn("--opt3", r)
        self.assertIn("--opt4", r)
        self.assertIn("--opt5", r)

    def test_default_hidden_aliases(self) -> None:
        self.builder.add_command_alias("hidden1", "cmd1", hide=True)
        self.builder.add_command_alias("hidden2", "cmd1", hide=True)
        self.builder.add_command_alias("hidden3", "cmd2", hide=True)
        self.builder.add_command_alias("show", "cmd1")
        self.builder.add_option_alias("--hide1", "--opt1", hide=True)
        self.builder.add_option_alias("--hide2", "--opt3", command="cmd3", hide=True)
        self.builder.add_option_alias("--hide2", "--opt2", command="cmd2", hide=True)
        r = self.helper.format_help()
        self.assertNotIn("hidden1", r)
        self.assertNotIn("hidden2", r)
        self.assertNotIn("hidden3", r)
        self.assertIn("show", r)
        self.assertNotIn("--hide1", r)
        self.assertNotIn("--hide2", r)

    def test_default_hidden_show_aliases(self) -> None:
        self.builder.add_command_alias("hidden1", "cmd1", hide=True)
        self.builder.add_command_alias("hidden2", "cmd1", hide=True)
        self.builder.add_command_alias("hidden3", "cmd2", hide=True)
        self.builder.add_command_alias("show", "cmd1")
        self.builder.add_option_alias("--hide1", "--opt1", hide=True)
        self.builder.add_option_alias("--hide2", "--opt3", command="cmd3", hide=True)
        self.builder.add_option_alias("--hide2", "--opt2", command="cmd2", hide=True)
        r = self.helper.format_help(show_hidden=True)
        self.assertIn("hidden1", r)
        self.assertIn("hidden2", r)
        self.assertIn("hidden3", r)
        self.assertIn("show", r)
        self.assertIn("--hide1", r)
        self.assertNotIn("--hide2", r)
