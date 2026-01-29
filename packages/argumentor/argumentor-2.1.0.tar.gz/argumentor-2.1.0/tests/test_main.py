# argumentor - a lightweight & copylefted library to work with command-line arguments
# Copyright (C) 2021-2026 Camelia Lavender <camelia@tblock.me>

from unittest import TestCase
from argumentor import Argumentor


class TestArgumentor(TestCase):

    def setUp(self) -> None:
        self.argm = Argumentor()

    def test_register_cmd(self) -> None:
        self.argm.register_command("foo", "bar", "f")
        self.assertListEqual(list(self.argm.commands.keys()), ["foo"])
        self.assertDictEqual(
            self.argm.command_aliases, {"bar": "foo", "f": "foo", "foo": "foo"}
        )

    def test_register_opts(self) -> None:
        self.argm.register_option("--foo", "--bar", "-f")
        self.assertListEqual(list(self.argm.options.keys()), ["--foo"])
        self.assertDictEqual(
            self.argm.option_aliases,
            {"--bar": {"*": "--foo"}, "-f": {"*": "--foo"}, "--foo": {"*": "--foo"}},
        )
