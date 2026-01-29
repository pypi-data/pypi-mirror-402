# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

from unittest import TestCase
from enum import Enum
from typing import List
from argumentor import Argumentor
from argumentor.exc import ParsingError


def set_up_argm() -> Argumentor:
    argm = Argumentor()
    argm.register_command(
        "bool1", "b1", "b", description="command that expects boolean value"
    )
    argm.register_command(
        "--bool2", "-B", description="command that expects boolean value"
    )
    argm.register_command(
        "int1",
        "i1",
        "i",
        description="command that expects integer value",
        value_type=int,
    )
    argm.register_command(
        "--int2",
        "-I",
        description="command that expects integer value",
        value_type=int,
    )
    argm.register_command(
        "str1",
        "s1",
        "s",
        description="command that expects string value",
        value_type=str,
    )
    argm.register_command(
        "--str2",
        "-S",
        description="command that expects string value",
        value_type=str,
    )
    argm.register_command(
        "list1",
        "l1",
        "l",
        description="command that expects list value",
        value_type=list,
    )
    argm.register_command(
        "--list2",
        "-L",
        description="command that expects list value",
        value_type=list,
    )

    argm.register_option(
        "--gbool1",
        "--gb1",
        "-g",
        description="global option that expects boolean value",
    )
    argm.register_option(
        "--gint1",
        "--gi1",
        "-G",
        description="global option that expects integer value",
        value_type=int,
    )
    argm.register_option(
        "--gstr1",
        "--gs1",
        "-f",
        description="global option that expects string value",
        value_type=str,
    )
    argm.register_option(
        "--glist1",
        "--gl1",
        "-F",
        description="global option that expects list value",
        value_type=list,
    )

    for command in ("bool1", "--bool2", "--str2", "--list2"):
        argm.register_option(
            "--bool1",
            "--b1",
            "-b",
            description="non-global option that expects boolean value",
            command=command,
        )
        argm.register_option(
            "--int1",
            "--i1",
            "-i",
            description="non-global option that expects integer value",
            command=command,
            value_type=int,
        )
        argm.register_option(
            "--str1",
            "--s1",
            "-s",
            description="non-global option that expects string value",
            command=command,
            value_type=str,
        )
        argm.register_option(
            "--list1",
            "--l1",
            "-l",
            description="non-global option that expects list value",
            command=command,
            value_type=list,
        )
    return argm


def is_short(arg: str) -> bool:
    return len(arg) == 1 or (len(arg) == 2 and arg[0] == "-")


class CombinationMethod(Enum):
    SEPARATE = " "
    EQUAL = "="
    EQUAL_SINGLE_QUOTES = "='"
    EQUAL_DOUBLE_QUOTES = '="'
    CONCAT = "+"
    CONCAT_SINGLE_QUOTES = "+'"
    CONCAT_DOUBLE_QUOTES = '+"'


def combine(alias: str, value: str | int, method: CombinationMethod):
    if isinstance(value, (int, str)):
        if method == CombinationMethod.SEPARATE:
            return [alias, str(value)]
        if method == CombinationMethod.EQUAL:
            return [f"{alias}={value}"]
        if method == CombinationMethod.EQUAL_SINGLE_QUOTES:
            return [f"{alias}='{value}'"]
        if method == CombinationMethod.EQUAL_DOUBLE_QUOTES:
            return [f'{alias}="{value}"']
        if method == CombinationMethod.CONCAT:
            return [f"{alias}{value}"]
        if method == CombinationMethod.CONCAT_SINGLE_QUOTES:
            return [f"{alias}'{value}'"]
        if method == CombinationMethod.CONCAT_DOUBLE_QUOTES:
            return [f'{alias}"{value}"']
    raise TypeError(f"unsupported type: {value}")


class TestIntegrationCmdOnly(TestCase):

    def setUp(self) -> None:
        self.argm = set_up_argm()

    def test_cmd_bool(self) -> None:
        for alias, cmd in self.argm.command_aliases.items():
            cmd_def = self.argm.commands[cmd]
            if cmd_def["value_type"] == bool:
                pcmd, popt = self.argm.parse([alias])
                self.assertDictEqual(pcmd, {cmd: True})
                self.assertDictEqual(popt, {})

    def test_cmd_int(self) -> None:
        for alias, cmd in self.argm.command_aliases.items():
            cmd_def = self.argm.commands[cmd]
            if cmd_def["value_type"] == int:
                if is_short(alias):
                    for combm in CombinationMethod:
                        alias_str = combine(alias, 10, combm)
                        pcmd, popt = self.argm.parse(alias_str)
                        self.assertDictEqual(pcmd, {cmd: 10})
                        self.assertDictEqual(popt, {})
                else:
                    for combm in (
                        CombinationMethod.SEPARATE,
                        CombinationMethod.EQUAL,
                        CombinationMethod.EQUAL_SINGLE_QUOTES,
                        CombinationMethod.EQUAL_DOUBLE_QUOTES,
                    ):
                        alias_str = combine(alias, 10, combm)
                        pcmd, popt = self.argm.parse(alias_str)
                        self.assertDictEqual(pcmd, {cmd: 10})
                        self.assertDictEqual(popt, {})

    def test_cmd_str(self) -> None:
        for alias, cmd in self.argm.command_aliases.items():
            cmd_def = self.argm.commands[cmd]
            if cmd_def["value_type"] == str:
                if is_short(alias):
                    for combm in CombinationMethod:
                        alias_str = combine(alias, "foobar", combm)
                        if combm == CombinationMethod.CONCAT:
                            # if combination method is set to CONCAT,
                            # args are: sfoobar, but will be standardized to:
                            # s -f oobar
                            self.assertRaises(ParsingError, self.argm.parse, alias_str)
                        else:
                            pcmd, popt = self.argm.parse(alias_str)
                            self.assertDictEqual(pcmd, {cmd: "foobar"})
                            self.assertDictEqual(popt, {})
                else:
                    for combm in (
                        CombinationMethod.SEPARATE,
                        CombinationMethod.EQUAL,
                        CombinationMethod.EQUAL_SINGLE_QUOTES,
                        CombinationMethod.EQUAL_DOUBLE_QUOTES,
                    ):
                        alias_str = combine(alias, "foobar", combm)
                        pcmd, popt = self.argm.parse(alias_str)
                        self.assertDictEqual(pcmd, {cmd: "foobar"})
                        self.assertDictEqual(popt, {})

    def test_cmd_list(self) -> None:
        for alias, cmd in self.argm.command_aliases.items():
            cmd_def = self.argm.commands[cmd]
            if cmd_def["value_type"] == list:
                if is_short(alias):
                    for combm in CombinationMethod:
                        alias_str = combine(alias, "foobar", combm)
                        if combm == CombinationMethod.CONCAT:
                            # if combination method is set to CONCAT,
                            # args are: sfoobar, but will be standardized to:
                            # s -f oobar
                            self.assertRaises(ParsingError, self.argm.parse, alias_str)
                        else:
                            pcmd, popt = self.argm.parse(alias_str)
                            self.assertDictEqual(pcmd, {cmd: ["foobar"]})
                            self.assertDictEqual(popt, {})
                else:
                    for combm in (
                        CombinationMethod.SEPARATE,
                        CombinationMethod.EQUAL,
                        CombinationMethod.EQUAL_SINGLE_QUOTES,
                        CombinationMethod.EQUAL_DOUBLE_QUOTES,
                    ):
                        alias_str = combine(alias, "foobar", combm)
                        pcmd, popt = self.argm.parse(alias_str)
                        self.assertDictEqual(pcmd, {cmd: ["foobar"]})
                        self.assertDictEqual(popt, {})
