# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

from unittest import TestCase
from argumentor.builder import Builder
from argumentor.const import Flags
from argumentor.exc import ParsingError
from argumentor.parser import Parser


class TestConvertValue(TestCase):

    def test_no_convert(self) -> None:
        self.assertEqual(Parser.convert_value("1", str), "1")

    def test_convert_int(self) -> None:
        self.assertEqual(Parser.convert_value("1", int), 1)

    def test_convert_int_error(self) -> None:
        self.assertIsNone(Parser.convert_value("a", int))


class TestIsSpecialOption(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_is_special(self) -> None:
        self.builder.add_option("--test", flags=Flags.SPECIAL)
        self.assertTrue(Parser.is_special_option(self.builder.options["--test"]["*"]))

    def test_is_not_special(self) -> None:
        self.builder.add_option("--test")
        self.assertFalse(Parser.is_special_option(self.builder.options["--test"]["*"]))


class TestStoreArgument(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()
        self.parser = Parser(self.builder)

    def test_expects_value_but_previous_unsatisfied(self) -> None:
        # this test should only run for options
        # commands do not behave the same way (they do not need
        # to be followed by their expected value)
        self.builder.add_option("--one", value_type=str)
        self.builder.add_option("--two", value_type=str)
        self.parser.store_argument(self.builder.options["--one"]["*"])
        # here the parser expects a value to be specified, but we specify another
        # option that expects a value instead
        self.assertRaises(
            ParsingError, self.parser.store_argument, self.builder.options["--two"]["*"]
        )

    def test_cmd_bool(self) -> None:
        self.builder.add_command("--test")
        self.parser.store_argument(self.builder.commands["--test"])
        self.assertTrue(self.parser.output_command["--test"])

    def test_opt_bool(self) -> None:
        self.builder.add_option("--test")
        self.parser.store_argument(self.builder.options["--test"]["*"])
        self.assertTrue(self.parser.output_options["--test"])

    def test_opt_expects(self) -> None:
        self.builder.add_option("--test", value_type=str)
        self.parser.store_argument(self.builder.options["--test"]["*"])
        self.assertEqual(self.parser.arguments["expects"]["option"], "--test")
        self.assertEqual(self.parser.arguments["expects"]["command"], "*")

    def test_opt_expects_list(self) -> None:
        self.builder.add_option("--test", value_type=list)
        self.parser.store_argument(self.builder.options["--test"]["*"])
        self.assertEqual(self.parser.arguments["allows"]["option"], "--test")
        self.assertEqual(self.parser.arguments["allows"]["command"], "*")

    def test_cmd_illegal_value(self) -> None:
        self.builder.add_command("--test", value_type=int)
        cmd = self.builder.commands["--test"]
        self.parser.store_argument(cmd)
        self.assertRaises(ParsingError, self.parser.store_argument, cmd, "a")

    def test_opt_illegal_value(self) -> None:
        self.builder.add_option("--test", value_type=int)
        opt = self.builder.options["--test"]["*"]
        self.parser.store_argument(opt)
        self.assertRaises(ParsingError, self.parser.store_argument, opt, "a")

    def test_cmd_expects_success(self) -> None:
        self.builder.add_command("--test", value_type=int)
        cmd = self.builder.commands["--test"]
        self.parser.store_argument(cmd)
        self.parser.store_argument(cmd, "4")
        self.assertEqual(self.parser.output_command["--test"], 4)

    def test_opt_expects_success(self) -> None:
        self.builder.add_option("--test", value_type=int)
        opt = self.builder.options["--test"]["*"]
        self.parser.store_argument(opt)
        self.parser.store_argument(opt, "4")
        self.assertEqual(self.parser.output_options["--test"], 4)

    def test_cmd_and_opt_expects_success(self) -> None:
        self.builder.add_command("--cmd", value_type=str)
        self.builder.add_option("--opt", value_type=str)
        cmd = self.builder.commands["--cmd"]
        opt = self.builder.options["--opt"]["*"]
        self.parser.store_argument(cmd)
        self.parser.store_argument(opt)
        self.parser.store_argument(opt, "opt-value")
        self.parser.store_argument(cmd, "cmd-value")
        self.assertEqual(self.parser.output_command["--cmd"], "cmd-value")
        self.assertEqual(self.parser.output_options["--opt"], "opt-value")

    def test_cmd_expects_list_success(self) -> None:
        self.builder.add_command("--test", value_type=list)
        cmd = self.builder.commands["--test"]
        self.parser.store_argument(cmd)
        self.parser.store_argument(cmd, "one")
        self.parser.store_argument(cmd, "two")
        self.assertListEqual(self.parser.output_command["--test"], ["one", "two"])

    def test_opt_expects_list_success(self) -> None:
        self.builder.add_option("--test", value_type=list)
        opt = self.builder.options["--test"]["*"]
        self.parser.store_argument(opt)
        self.parser.store_argument(opt, "one")
        self.parser.store_argument(opt, "two")
        self.assertListEqual(self.parser.output_options["--test"], ["one", "two"])

    def test_cmd_and_opt_expects_list_success(self) -> None:
        # this example is purely theoretical, it is probably not
        # possible to do this at a more integrated level, because
        # because self.arguments is emptied when option is stored
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_option("--opt", value_type=list)
        cmd = self.builder.commands["--cmd"]
        opt = self.builder.options["--opt"]["*"]
        self.parser.store_argument(cmd)
        self.parser.store_argument(cmd, "cmd-one")
        self.parser.store_argument(opt)
        self.parser.store_argument(opt, "opt-one")
        self.parser.store_argument(opt, "opt-two")
        self.parser.store_argument(cmd, "cmd-two")
        self.assertListEqual(
            self.parser.output_command["--cmd"], ["cmd-one", "cmd-two"]
        )
        self.assertListEqual(
            self.parser.output_options["--opt"], ["opt-one", "opt-two"]
        )


class TestParse(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_cmd_defined_but_not_first_arg(self) -> None:
        self.builder.add_command("--cmd")
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--opt"])
        self.assertRaises(ParsingError, parser.parse)

    def test_cmd_bool(self) -> None:
        self.builder.add_command("--cmd")
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": True})
        self.assertDictEqual(options, {})

    def test_cmd_opt_bool(self) -> None:
        self.builder.add_command("--cmd")
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd", "--opt"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": True})
        self.assertDictEqual(options, {"--opt": True})

    def test_cmd_expects(self) -> None:
        self.builder.add_command("--cmd", value_type=str)
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd", "test"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": "test"})
        self.assertDictEqual(options, {})

    def test_cmd_opt_expects(self) -> None:
        self.builder.add_command("--cmd", value_type=str)
        self.builder.add_option("--opt", value_type=str)
        parser = Parser(self.builder, ["--cmd", "--opt", "opt-value", "cmd-value"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": "cmd-value"})
        self.assertDictEqual(options, {"--opt": "opt-value"})

    def test_cmd_expects_list(self) -> None:
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd", "a", "--opt", "b"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": ["a", "b"]})
        self.assertDictEqual(options, {"--opt": True})

    def test_cmd_opt_expects_list(self) -> None:
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_option("--opt", value_type=list)
        parser = Parser(self.builder, ["--cmd", "cmd-1", "--opt", "opt-1", "opt-2"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": ["cmd-1"]})
        self.assertDictEqual(options, {"--opt": ["opt-1", "opt-2"]})

    def test_cmd_opt_alias_expects_list(self) -> None:
        # this achieves nothing more than the previous test,
        # but it is a safeguard against future modifications
        # that may break alias support
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_command_alias("--cmd-alias", "--cmd")
        self.builder.add_option("--opt", value_type=list)
        self.builder.add_option_alias("--opt-alias", "--opt")
        parser = Parser(
            self.builder, ["--cmd-alias", "cmd-1", "--opt-alias", "opt-1", "opt-2"]
        )
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": ["cmd-1"]})
        self.assertDictEqual(options, {"--opt": ["opt-1", "opt-2"]})

    def test_cmd_arg_invalid(self) -> None:
        self.builder.add_command("--cmd", value_type=str)
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd", "value", "invalid"])
        self.assertRaises(ParsingError, parser.parse)

    def test_opt_arg_invalid(self) -> None:
        self.builder.add_command("--cmd")
        self.builder.add_option("--opt", value_type=str)
        parser = Parser(self.builder, ["--cmd", "--opt", "value", "invalid"])
        self.assertRaises(ParsingError, parser.parse)

    def test_opt_command_specific(self) -> None:
        self.builder.add_command("--cmd")
        self.builder.add_option("--opt", "--cmd", value_type=str)
        parser = Parser(self.builder, ["--cmd", "--opt", "value"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": True})
        self.assertDictEqual(options, {"--opt": "value"})

    def test_opt_command_incompatible(self) -> None:
        self.builder.add_command("--cmd")
        self.builder.add_command("--cmd2")
        self.builder.add_option("--opt", "--cmd", value_type=str)
        parser = Parser(self.builder, ["--cmd2", "--opt", "value"])
        self.assertRaises(ParsingError, parser.parse)

    def test_cmd_allow_followed_by_opts(self) -> None:

        self.builder.add_command("--subscribe", value_type=list)
        self.builder.add_command_alias("-S", "--subscribe")
        self.builder.add_option("--with-sync", command="--subscribe")
        self.builder.add_option("--with-update", command="--subscribe")
        self.builder.add_option("--force")
        self.builder.add_option_alias("-y", "--with-sync", command="--subscribe")
        self.builder.add_option_alias("-u", "--with-update", command="--subscribe")
        self.builder.add_option_alias("-f", "--force")
        parser = Parser(self.builder, ["-Syuf", "test"])
        cmd, opts = parser.parse()
        self.assertDictEqual(cmd, {"--subscribe": ["test"]})
        self.assertDictEqual(
            opts, {"--with-sync": True, "--with-update": True, "--force": True}
        )


class TestValidate(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_cmd_arg_expected(self) -> None:
        self.builder.add_command("--cmd", value_type=str)
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd"])
        self.assertRaises(ParsingError, parser.parse)

    def test_opt_arg_expected(self) -> None:
        self.builder.add_option("--opt", value_type=str)
        parser = Parser(self.builder, ["--opt"])
        self.assertRaises(ParsingError, parser.parse)

    def test_cmd_arg_list_expected(self) -> None:
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_option("--opt")
        parser = Parser(self.builder, ["--cmd", "--opt"])
        self.assertRaises(ParsingError, parser.parse)

    def test_opt_arg_list_expected(self) -> None:
        self.builder.add_option("--opt", value_type=list)
        parser = Parser(self.builder, ["--opt"])
        self.assertRaises(ParsingError, parser.parse)

    def test_cmd_arg_expected_but_special_opt(self) -> None:
        self.builder.add_command("--cmd", value_type=str)
        self.builder.add_option("--opt", flags=Flags.SPECIAL)
        parser = Parser(self.builder, ["--cmd", "--opt"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": None})
        self.assertDictEqual(options, {"--opt": True})

    def test_cmd_arg_list_expected_but_special_opt(self) -> None:
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_option("--opt", flags=Flags.SPECIAL)
        parser = Parser(self.builder, ["--cmd", "--opt"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": None})
        self.assertDictEqual(options, {"--opt": True})

    def test_cmd_arg_list_expected_but_special_opt_expects(self) -> None:
        self.builder.add_command("--cmd", value_type=list)
        self.builder.add_option("--opt", value_type=str, flags=Flags.SPECIAL)
        parser = Parser(self.builder, ["--cmd", "--opt", "a"])
        command, options = parser.parse()
        self.assertDictEqual(command, {"--cmd": None})
        self.assertDictEqual(options, {"--opt": "a"})

    def test_opt_arg_list_expected_but_special_opt(self) -> None:
        self.builder.add_option("--opt", value_type=list)
        self.builder.add_option("--opt2", flags=Flags.SPECIAL)
        parser = Parser(self.builder, ["--opt", "--opt2"])
        command, options = parser.parse()
        self.assertDictEqual(command, {})
        self.assertDictEqual(options, {"--opt": ["--opt2"]})

    def test_opt_missing_mandatory_opt(self) -> None:
        self.builder.add_option("--opt", flags=Flags.REQUIRED)
        parser = Parser(self.builder, [])
        self.assertRaises(ParsingError, parser.parse)

    def test_opt_default_value(self) -> None:
        self.builder.add_option("--level", value_type=int, default_value=3)
        parser = Parser(self.builder, [])
        command, options = parser.parse()
        self.assertDictEqual(command, {})
        self.assertDictEqual(options, {"--level": 3})

    def test_opt_default_value_overwrite(self) -> None:
        self.builder.add_option("--level", value_type=int, default_value=3)
        parser = Parser(self.builder, ["--level=2"])
        command, options = parser.parse()
        self.assertDictEqual(command, {})
        self.assertDictEqual(options, {"--level": 2})

    def test_skip_all(self) -> None:
        self.builder.add_command("run", value_type=str)
        self.builder.add_command("help")
        self.builder.add_option("--args", value_type=list)
        self.builder.add_option("--verbose", command="help")
        self.builder.add_option_alias("-v", "--verbose", command="help")
        self.builder.add_option_alias("-k", "--verbose", command="help")
        args = [
            "run",
            "command",
            "--args",
            "--",
            "--verbose",
            "-vkn",
            "--args=test1",
            "example",
        ]
        parser = Parser(self.builder, args)
        command, options = parser.parse()
        self.assertDictEqual(command, {"run": "command"})
        self.assertDictEqual(
            options, {"--args": ["--verbose", "-vkn", "--args=test1", "example"]}
        )
