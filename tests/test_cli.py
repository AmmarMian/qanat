# ========================================
# FileName: test_cli.py
# Date: 20 avril 2023 - 11:50
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Test the CLI
# =========================================

from qanat import cli
import unittest
import tempfile
import os
import git
from unittest.mock import patch


class CLIMainTest(unittest.TestCase):
    """Test the main parser element of the CLI."""

    def setUp(self):
        self.cli = cli.QanatCli()

    def test_nocommand(self):
        """Test the parser without a command."""
        args = self.cli.main_parser.parse_args([])
        self.assertIsNone(args.command)

    def test_command(self):
        """Test the parser with a command."""
        args = self.cli.main_parser.parse_args(["init", "path"])
        self.assertEqual(args.command, "init")

        args = self.cli.main_parser.parse_args(["status"])
        self.assertEqual(args.command, "status")

    def test_version(self):
        """Test the version flag."""
        with self.assertRaises(SystemExit):
            self.cli.main_parser.parse_args(["--version"])

    def test_help(self):
        """Test the help flag."""
        with self.assertRaises(SystemExit):
            self.cli.main_parser.parse_args(["--help"])


class CLIInitErrorsTest(unittest.TestCase):
    """Test the init subparser element of the CLI for typical errors."""

    def setUp(self):
        self.cli = cli.QanatCli()
        self.init_subparser = self.cli.subparsers.choices["init"]

    def test_initnopath(self):
        """Test the init subparser without a path."""
        with self.assertRaises(SystemExit):
            self.init_subparser.parse_args([])

    def test_initpath_notexist(self):
        """Test the init subparser with a path that does not exist."""
        with self.assertRaises(SystemExit):
            with tempfile.TemporaryDirectory() as tmpdirname:
                self.init_subparser.parse_args([tmpdirname])


class CLIInitNotGitTest(unittest.TestCase):
    """Test the init subparser element of the CLI case when
    the path is not a git repository."""

    def setUp(self):
        self.cli = cli.QanatCli()
        self.init_subparser = self.cli.subparsers.choices["init"]

    @patch("builtins.input", return_value="n")
    def test_initpath_notgit_nocreate(self):
        """Test if cli exits when the user doen not want to
        create a git repository after being prompted."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            with self.assertRaises(SystemExit):
                self.init_subparser.parse_args([tmpdirname])

    @patch("builtins.input", return_value="y")
    def test_initpath_notgit_create(self):
        """Test that the repertory is initialized as a git repository
        when the user wants to."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.init_subparser.parse_args([tmpdirname])
            self.assertTrue(git.Repo(tmpdirname).git_dir)


class CLIInitQanatDir(unittest.TestCase):
    """Test the init subparser element of the CLI for the existence/creation
    of the qanat directory."""

    def setUp(self):
        self.cli = cli.QanatCli()
        self.init_subparser = self.cli.subparsers.choices["init"]

    def test_initpath_qanatdir_notexist(self):
        """Test that the qanat directory is created when it does not exist."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.init_subparser.parse_args([tmpdirname])
            self.assertTrue(os.path.isdir(os.path.join(tmpdirname, ".qanat")))

    def test_initpath_qanatdir_exist(self):
        """Test that nothing happens when the qanat directory already
        exists."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.mkdir(os.path.join(tmpdirname, ".qanat"))
            self.init_subparser.parse_args([tmpdirname])
            self.assertTrue(os.path.isdir(os.path.join(tmpdirname, ".qanat")))
