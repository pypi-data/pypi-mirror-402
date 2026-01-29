# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

from unittest import TestCase
from argumentor.builder import Builder
from argumentor.std import Standardizer


class TestGetPrefix(TestCase):

    def test_one_dash(self) -> None:
        r = Standardizer.get_prefix("-ab")
        self.assertEqual(r, ("-", "ab"))

    def test_two_dashes(self) -> None:
        r = Standardizer.get_prefix("--ab")
        self.assertEqual(r, ("-", "-ab"))

    def test_no_dash(self) -> None:
        r = Standardizer.get_prefix("a")
        self.assertEqual(r, ("", "a"))

    def test_empty(self) -> None:
        r = Standardizer.get_prefix("")
        self.assertEqual(r, ("", ""))

    def test_is_only_dash(self) -> None:
        r = Standardizer.get_prefix("-")
        self.assertEqual(r, ("-", ""))


class TestUnquote(TestCase):

    def test_no_quotes(self) -> None:
        r = Standardizer.unquote("test")
        self.assertEqual(r, "test")

    def test_single_quotes(self) -> None:
        r = Standardizer.unquote("'test'")
        self.assertEqual(r, "test")

    def test_single_quotes_not_closed(self) -> None:
        r = Standardizer.unquote("'test")
        self.assertEqual(r, "'test")

    def test_single_quotes_not_opened(self) -> None:
        r = Standardizer.unquote("test'")
        self.assertEqual(r, "test'")

    def test_double_quotes(self) -> None:
        r = Standardizer.unquote('"test"')
        self.assertEqual(r, "test")

    def test_double_quotes_not_closed(self) -> None:
        r = Standardizer.unquote('"test')
        self.assertEqual(r, '"test')

    def test_double_quotes_not_opened(self) -> None:
        r = Standardizer.unquote('test"')
        self.assertEqual(r, 'test"')


class TestStandardizeSimple(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_no_cmd_no_opt(self) -> None:
        standardizer = Standardizer(self.builder)
        args = ["foo", "bar", "-ab1", "2", "--test", "--value=a", "foo2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_cmd_no_opt(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        args = ["cmd", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_cmd_no_opt_with_equal(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        args = ["cmd=value", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["cmd", "value", "-a", "2"], r)

    def test_cmd_no_opt_with_equal_single_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        args = ["cmd='value'", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["cmd", "value", "-a", "2"], r)

    def test_cmd_no_opt_with_equal_double_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        args = ['cmd="value"', "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["cmd", "value", "-a", "2"], r)

    def test_cmd_alias_no_opt(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("alias", "cmd")
        args = ["alias", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_cmd_alias_no_opt_with_equal(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("alias", "cmd")
        args = ["alias=value", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["alias", "value", "-a", "2"], r)

    def test_cmd_alias_no_opt_with_equal_single_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("alias", "cmd")
        args = ["alias='value'", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["alias", "value", "-a", "2"], r)

    def test_cmd_alias_no_opt_with_equal_double_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("alias", "cmd")
        args = ['alias="value"', "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["alias", "value", "-a", "2"], r)

    def test_cmd_short_no_dash_no_opt(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("c", "cmd")
        args = ["c", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_cmd_short_no_dash_no_opt_with_combined(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("c", "cmd")
        args = ["cvalue", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["c", "value", "-a", "2"], r)

    def test_cmd_short_no_dash_no_opt_with_combined_single_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("c", "cmd")
        args = ["c'value'", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["c", "value", "-a", "2"], r)

    def test_cmd_short_no_dash_no_opt_with_combined_double_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("cmd")
        self.builder.add_command_alias("c", "cmd")
        args = ['c"value"', "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["c", "value", "-a", "2"], r)

    def test_no_cmd_opt(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        args = ["--opt", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_no_cmd_opt_with_equal(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        args = ["--opt=value", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["--opt", "value", "-a", "2"], r)

    def test_no_cmd_opt_with_equal_single_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        args = ["--opt='value'", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["--opt", "value", "-a", "2"], r)

    def test_no_cmd_opt_with_equal_double_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        args = ['--opt="value"', "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["--opt", "value", "-a", "2"], r)

    def test_no_cmd_opt_alias(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("--alias", "--opt")
        args = ["--alias", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_no_cmd_opt_alias_with_equal(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("--alias", "--opt")
        args = ["--alias=value", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["--alias", "value", "-a", "2"], r)

    def test_no_cmd_opt_alias_with_equal_single_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("--alias", "--opt")
        args = ["--alias='value'", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["--alias", "value", "-a", "2"], r)

    def test_no_cmd_opt_alias_with_equal_double_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("--alias", "--opt")
        args = ['--alias="value"', "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["--alias", "value", "-a", "2"], r)

    def test_no_cmd_opt_short_no_dash(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("-o", "--opt")
        args = ["-o", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(args, r)

    def test_no_cmd_opt_short_no_dash_with_combined(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("-o", "--opt")
        args = ["-ovalue", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["-o", "value", "-a", "2"], r)

    def test_no_cmd_opt_short_no_dash_with_combined_single_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("-o", "--opt")
        args = ["-o'value'", "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["-o", "value", "-a", "2"], r)

    def test_no_cmd_opt_short_no_dash_with_combined_double_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_option("--opt")
        self.builder.add_option_alias("-o", "--opt")
        args = ['-o"value"', "-a", "2"]
        r = standardizer.standardize(args)
        self.assertEqual(["-o", "value", "-a", "2"], r)


class TestStandardizeComplex(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_cmd_twice(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("foo")
        self.builder.add_command("bar")
        args = ["foo=1", "bar=2"]
        r = standardizer.standardize(args)
        self.assertEqual(["foo", "1", "bar=2"], r)

    def test_cmd_expects_value_but_got_opt(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("foo", value_type=str)
        self.builder.add_option("--bar", value_type=str)
        args = ["foo", "--bar=a", "test"]
        r = standardizer.standardize(args)
        self.assertEqual(["foo", "--bar", "a", "test"], r)

    def test_opt_combine(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("foo", value_type=str)
        self.builder.add_option("-a")
        self.builder.add_option("-b")
        self.builder.add_option("-c")
        args = ["foo", "-abc", "test"]
        r = standardizer.standardize(args)
        self.assertEqual(["foo", "-a", "-b", "-c", "test"], r)

    def test_opt_combine_with_excepted_value(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("foo", value_type=str)
        self.builder.add_option("-a")
        self.builder.add_option("-b", value_type=str)
        self.builder.add_option("-c")
        args = ["foo", "-abc", "test"]
        r = standardizer.standardize(args)
        self.assertEqual(["foo", "-a", "-b", "c", "test"], r)

    def test_opt_combine_not_same_prefix_start_with_prefix(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("foo", value_type=str)
        self.builder.add_option("-a")
        self.builder.add_option("b")
        args = ["foo", "-ab", "test"]
        r = standardizer.standardize(args)
        self.assertEqual(["foo", "-a", "b", "test"], r)

    def test_opt_combine_not_same_prefix_start_no_prefix(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("foo", value_type=str)
        self.builder.add_option("a")
        self.builder.add_option("-b")
        args = ["foo", "ab", "test"]
        r = standardizer.standardize(args)
        self.assertEqual(["foo", "a", "-b", "test"], r)

    def test_issue009(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("-Q", value_type=str)
        self.builder.add_option("-q")
        args = ["-Qqfoo"]
        r = standardizer.standardize(args)
        self.assertEqual(["-Q", "-q", "foo"], r)

    def test_issue009_quotes(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("-Q", value_type=str)
        self.builder.add_option("-q")
        args = ["-Q'q'foo"]
        r = standardizer.standardize(args)
        self.assertEqual(["-Q", "'q'foo"], r)

    def test_issue009_quotes_no_value(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("-Q", value_type=str)
        self.builder.add_option("-q")
        args = ["-Q'q'"]
        r = standardizer.standardize(args)
        self.assertEqual(["-Q", "q"], r)

    def test_issue009_safecheck(self) -> None:
        standardizer = Standardizer(self.builder)
        self.builder.add_command("-Q", value_type=str)
        self.builder.add_option("-q", value_type=str)
        args = ["-Qqfoo", "-qq", "bar"]
        r = standardizer.standardize(args)
        self.assertEqual(["-Q", "-q", "foo", "-q", "q", "bar"], r)

    def test_skip_all(self) -> None:
        standardizer = Standardizer(self.builder)
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
        r = standardizer.standardize(args)
        self.assertEqual(args, r)
