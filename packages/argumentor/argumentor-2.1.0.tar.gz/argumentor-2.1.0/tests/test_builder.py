# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

from unittest import TestCase
from argumentor import Flags
from argumentor.builder import Builder
from argumentor.exc import (
    CommandExistsException,
    CommandNotFoundException,
    OptionExistsException,
    OptionNotFoundException,
)


class TestAddCommand(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_cmd_basic(self) -> None:
        self.builder.add_command(
            "foo", description="example command", value_type=str, value_name="STR"
        )
        self.builder.add_command("bar")
        self.assertDictEqual(
            self.builder.commands,
            {
                "foo": {
                    "command": "foo",
                    "description": "example command",
                    "value_type": str,
                    "value_name": "STR",
                },
                "bar": {
                    "command": "bar",
                    "description": "",
                    "value_type": bool,
                    "value_name": "",
                },
            },
        )
        self.assertDictEqual(self.builder.command_aliases, {"foo": "foo", "bar": "bar"})

    def test_cmd_is_global(self) -> None:
        self.assertRaises(CommandExistsException, self.builder.add_command, "*")

    def test_cmd_exists(self) -> None:
        self.builder.add_command("foo", description="example command")
        self.assertRaises(CommandExistsException, self.builder.add_command, "foo")

    def test_alias_exists(self) -> None:
        self.builder.add_command("foo", description="example command")
        self.builder.add_command_alias("bar", "foo")
        self.assertRaises(CommandExistsException, self.builder.add_command, "bar")

    def test_invalid_value_type(self) -> None:
        self.assertRaises(
            ValueError, self.builder.add_command, "foo", value_type=object
        )


class TestAddCommandAlias(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_alias_basic(self) -> None:
        self.builder.add_command(
            "foo", description="example command", value_type=str, value_name="STR"
        )
        self.builder.add_command("bar")
        self.builder.add_command_alias("foo-a", "foo")
        self.builder.add_command_alias("bar-a", "bar")
        self.assertDictEqual(
            self.builder.commands,
            {
                "foo": {
                    "command": "foo",
                    "description": "example command",
                    "value_type": str,
                    "value_name": "STR",
                },
                "bar": {
                    "command": "bar",
                    "description": "",
                    "value_type": bool,
                    "value_name": "",
                },
            },
        )
        self.assertDictEqual(
            self.builder.command_aliases,
            {"foo": "foo", "foo-a": "foo", "bar": "bar", "bar-a": "bar"},
        )

    def test_alias_is_global(self) -> None:
        self.builder.add_command("foo")
        self.assertRaises(
            CommandExistsException, self.builder.add_command_alias, "*", "foo"
        )

    def test_cmd_is_global(self) -> None:
        self.assertRaises(
            CommandNotFoundException, self.builder.add_command_alias, "bar", "*"
        )

    def test_alias_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_command_alias("bar", "foo")
        self.builder.add_command("foo2")
        self.assertRaises(
            CommandExistsException, self.builder.add_command_alias, "bar", "foo2"
        )

    def test_cmd_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_command("bar")
        self.assertRaises(
            CommandExistsException, self.builder.add_command_alias, "bar", "foo"
        )

    def test_cmd_not_found(self) -> None:
        self.assertRaises(
            CommandNotFoundException, self.builder.add_command_alias, "bar", "foo"
        )


class TestAddOption(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_opt_basic(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option(
            "--foo",
            "foo",
            description="example option",
            value_type=str,
            default_value="test",
            value_name="STR",
            flags=Flags.REQUIRED,
        )
        self.builder.add_command("bar")
        self.builder.add_option("--foo", "bar")
        self.assertEqual(
            self.builder.options,
            {
                "--foo": {
                    "foo": {
                        "command": "foo",
                        "default_value": "test",
                        "description": "example option",
                        "flags": Flags.REQUIRED,
                        "option": "--foo",
                        "value_name": "STR",
                        "value_type": str,
                    },
                    "bar": {
                        "command": "bar",
                        "default_value": None,
                        "description": "",
                        "flags": None,
                        "option": "--foo",
                        "value_name": "",
                        "value_type": bool,
                    },
                }
            },
        )
        self.assertDictEqual(
            self.builder.option_aliases,
            {"--foo": {"foo": "--foo", "bar": "--foo"}},
        )

    def test_cmd_not_found(self) -> None:
        self.assertRaises(
            CommandNotFoundException, self.builder.add_option, "--bar", "foo"
        )

    def test_opt_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", "foo")
        self.assertRaises(
            OptionExistsException, self.builder.add_option, "--foo", "foo"
        )

    def test_opt_global_exists(self) -> None:
        self.builder.add_option("--foo")
        self.builder.add_command("foo")
        self.assertRaises(
            OptionExistsException, self.builder.add_option, "--foo", "foo"
        )

    def test_global_opt_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", "foo")
        self.assertRaises(OptionExistsException, self.builder.add_option, "--foo")

    def test_invalid_value_type(self) -> None:
        self.assertRaises(
            ValueError, self.builder.add_option, "--foo", value_type=object
        )

    def test_invalid_default_value(self) -> None:
        self.assertRaises(
            ValueError,
            self.builder.add_option,
            "--foo",
            value_type=int,
            default_value="string",
        )


class TestAddOptionAlias(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_alias_basic(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option(
            "--foo",
            "foo",
            description="example option",
            value_type=str,
            default_value="test",
            value_name="STR",
            flags=Flags.REQUIRED,
        )
        self.builder.add_command("bar")
        self.builder.add_option("--foo", "bar")
        self.builder.add_option_alias("--foo-a", "--foo", command="foo")
        self.builder.add_option_alias("--foo-b", "--foo", command="foo")
        self.builder.add_option_alias("--bar-1", "--foo", command="bar")
        self.builder.add_option_alias("--foo-b", "--foo", command="bar")
        self.assertEqual(
            self.builder.options,
            {
                "--foo": {
                    "foo": {
                        "command": "foo",
                        "default_value": "test",
                        "description": "example option",
                        "flags": Flags.REQUIRED,
                        "option": "--foo",
                        "value_name": "STR",
                        "value_type": str,
                    },
                    "bar": {
                        "command": "bar",
                        "default_value": None,
                        "description": "",
                        "flags": None,
                        "option": "--foo",
                        "value_name": "",
                        "value_type": bool,
                    },
                }
            },
        )
        self.assertDictEqual(
            self.builder.option_aliases,
            {
                "--foo": {"foo": "--foo", "bar": "--foo"},
                "--foo-a": {"foo": "--foo"},
                "--foo-b": {"foo": "--foo", "bar": "--foo"},
                "--bar-1": {"bar": "--foo"},
            },
        )

    def test_cmd_not_found(self) -> None:
        self.assertRaises(
            CommandNotFoundException,
            self.builder.add_option_alias,
            "--bar",
            "--foo",
            command="foo",
        )

    def test_opt_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", command="foo")
        self.assertRaises(
            OptionExistsException,
            self.builder.add_option_alias,
            "--foo",
            "--foo",
            command="foo",
        )

    def test_alias_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", command="foo")
        self.builder.add_option_alias("--bar", "--foo", command="foo")
        self.assertRaises(
            OptionExistsException,
            self.builder.add_option_alias,
            "--bar",
            "--foo",
            command="foo",
        )

    def test_opt_global_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", command="foo")
        self.builder.add_option("--bar")
        self.assertRaises(
            OptionExistsException,
            self.builder.add_option_alias,
            "--bar",
            "--foo",
            command="foo",
        )

    def test_opt_not_found(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_command("bar")
        self.builder.add_option("--foo", command="foo")
        self.assertRaises(
            OptionNotFoundException,
            self.builder.add_option_alias,
            "--bar",
            "--foo",
            command="bar",
        )

    def test_opt_global_not_found(self) -> None:
        self.assertRaises(
            OptionNotFoundException, self.builder.add_option_alias, "--bar", "--foo"
        )

    def test_global_opt_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", command="foo")
        self.builder.add_option("--bar")
        self.assertRaises(
            OptionExistsException, self.builder.add_option_alias, "--foo", "--bar"
        )

    def test_alias_global_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", command="foo")
        self.builder.add_option("--bar")
        self.builder.add_option_alias("--bar2", "--bar")
        self.assertRaises(
            OptionExistsException,
            self.builder.add_option_alias,
            "--bar2",
            "--foo",
            command="foo",
        )

    def test_global_alias_exists(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_option("--foo", command="foo")
        self.builder.add_option("--bar")
        self.builder.add_option_alias("--foo2", "--foo", command="foo")
        self.assertRaises(
            OptionExistsException, self.builder.add_option_alias, "--foo2", "--bar"
        )


class TestGetAliases(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_cmd_not_found(self) -> None:
        r = list(self.builder.get_aliases("foo"))
        self.assertListEqual(r, [])

    def test_opt_not_found(self) -> None:
        r = list(self.builder.get_aliases("--foo", command="foo"))
        self.assertListEqual(r, [])

    def test_cmd(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_command("bar")
        self.builder.add_command_alias("foo1", "foo")
        self.builder.add_command_alias("foo2", "foo")
        self.builder.add_command_alias("bar1", "bar")
        r = list(self.builder.get_aliases("foo"))
        self.assertListEqual(r, ["foo", "foo1", "foo2"])

    def test_opt(self) -> None:
        self.builder.add_command("foo")
        self.builder.add_command_alias("foo1", "foo")
        self.builder.add_command_alias("foo2", "foo")
        self.builder.add_option("--foo", command="foo")
        self.builder.add_option_alias("--foo1", "--foo", command="foo")
        self.builder.add_option_alias("--foo2", "--foo", command="foo")
        self.builder.add_option("--bar")
        self.builder.add_option_alias("--bar1", "--bar")
        r = list(self.builder.get_aliases("--foo", command="foo"))
        self.assertListEqual(r, ["--foo", "--foo1", "--foo2"])


class TestGetOpts(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()

    def test_cmd_not_found(self) -> None:
        r = list(self.builder.get_options_for_command("foo"))
        self.assertListEqual(r, [])

    def test_get_opts(self) -> None:
        self.builder.add_option("--foo")
        self.builder.add_option_alias("--foo1", "--foo")
        self.builder.add_option("--fooo")
        self.builder.add_command("bar")
        self.builder.add_option("--bar", command="bar")
        r = list(self.builder.get_options_for_command("*"))
        self.assertListEqual(
            r,
            [
                {
                    "command": "*",
                    "default_value": None,
                    "description": "",
                    "flags": None,
                    "option": "--foo",
                    "value_name": "",
                    "value_type": bool,
                },
                {
                    "command": "*",
                    "default_value": None,
                    "description": "",
                    "flags": None,
                    "option": "--fooo",
                    "value_name": "",
                    "value_type": bool,
                },
            ],
        )


class TestExpectsArgs(TestCase):

    def setUp(self) -> None:
        self.builder = Builder()
        self.builder.add_command("bool", value_type=bool)
        self.builder.add_command("str", value_type=str)
        self.builder.add_command("int", value_type=int)
        self.builder.add_command("list", value_type=list)
        self.builder.add_command("foo")
        self.builder.add_command_alias("bar", "foo")
        self.builder.add_option("--bool", command="foo", value_type=bool)
        self.builder.add_option("--str", command="foo", value_type=str)
        self.builder.add_option("--int", command="foo", value_type=int)
        self.builder.add_option("--list", command="foo", value_type=list)
        self.builder.add_option("--gbool", value_type=bool)
        self.builder.add_option("--gstr", value_type=str)
        self.builder.add_option("--gint", value_type=int)
        self.builder.add_option("--glist", value_type=list)

    def test_cmd_not_found(self) -> None:
        self.assertFalse(self.builder.expects_argument("none"))

    def test_cmd_bool(self) -> None:
        self.assertFalse(self.builder.expects_argument("bool"))

    def test_cmd_alias_bool(self) -> None:
        self.builder.add_command_alias("b", "bool")
        self.assertFalse(self.builder.expects_argument("b"))

    def test_cmd_str(self) -> None:
        self.assertTrue(self.builder.expects_argument("str"))

    def test_cmd_alias_str(self) -> None:
        self.builder.add_command_alias("s", "str")
        self.assertTrue(self.builder.expects_argument("s"))

    def test_cmd_int(self) -> None:
        self.assertTrue(self.builder.expects_argument("int"))

    def test_cmd_alias_int(self) -> None:
        self.builder.add_command_alias("i", "int")
        self.assertTrue(self.builder.expects_argument("i"))

    def test_cmd_list(self) -> None:
        self.assertTrue(self.builder.expects_argument("list"))

    def test_cmd_alias_list(self) -> None:
        self.builder.add_command_alias("l", "list")
        self.assertTrue(self.builder.expects_argument("l"))

    def test_opt_not_found(self) -> None:
        self.assertFalse(self.builder.expects_argument("--none", command_alias="bar"))

    def test_opt_bool(self) -> None:
        self.assertFalse(self.builder.expects_argument("--bool", command_alias="bar"))

    def test_opt_alias_bool(self) -> None:
        self.builder.add_option_alias("-b", "--bool", command="foo")
        self.assertFalse(self.builder.expects_argument("-b", command_alias="bar"))

    def test_opt_str(self) -> None:
        self.assertTrue(self.builder.expects_argument("--str", command_alias="bar"))

    def test_opt_alias_str(self) -> None:
        self.builder.add_option_alias("-s", "--str", command="foo")
        self.assertTrue(self.builder.expects_argument("-s", command_alias="bar"))

    def test_opt_int(self) -> None:
        self.assertTrue(self.builder.expects_argument("--int", command_alias="bar"))

    def test_opt_alias_int(self) -> None:
        self.builder.add_option_alias("-i", "--int", command="foo")
        self.assertTrue(self.builder.expects_argument("-i", command_alias="bar"))

    def test_opt_list(self) -> None:
        self.assertTrue(self.builder.expects_argument("--list", command_alias="bar"))

    def test_opt_alias_list(self) -> None:
        self.builder.add_option_alias("-l", "--list", command="foo")
        self.assertTrue(self.builder.expects_argument("-l", command_alias="bar"))

    def test_gopt_not_found(self) -> None:
        self.assertFalse(self.builder.expects_argument("--none", command_alias="*"))

    def test_gopt_bool(self) -> None:
        self.assertFalse(self.builder.expects_argument("--gbool", command_alias="*"))

    def test_gopt_alias_bool(self) -> None:
        self.builder.add_option_alias("-b", "--gbool")
        self.assertFalse(self.builder.expects_argument("-b", command_alias="*"))

    def test_gopt_str(self) -> None:
        self.assertTrue(self.builder.expects_argument("--gstr", command_alias="*"))

    def test_gopt_alias_str(self) -> None:
        self.builder.add_option_alias("-s", "--gstr")
        self.assertTrue(self.builder.expects_argument("-s", command_alias="*"))

    def test_gopt_int(self) -> None:
        self.assertTrue(self.builder.expects_argument("--gint", command_alias="*"))

    def test_gopt_alias_int(self) -> None:
        self.builder.add_option_alias("-i", "--gint")
        self.assertTrue(self.builder.expects_argument("-i", command_alias="*"))

    def test_gopt_list(self) -> None:
        self.assertTrue(self.builder.expects_argument("--glist", command_alias="*"))

    def test_gopt_alias_list(self) -> None:
        self.builder.add_option_alias("-l", "--glist")
        self.assertTrue(self.builder.expects_argument("-l", command_alias="*"))
