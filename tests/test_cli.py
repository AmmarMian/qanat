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
# import tempfile
# import os
# import git
# from unittest.mock import patch
from click.testing import CliRunner


# Test main commands of CLI
class CLIMainTest(unittest.TestCase):
    """Test the main commands and options of the cli"""

    def setUp(self):
        self.runner = CliRunner()

    def test_nocommand(self):
        """Test the parser without a command. Should exit with no error."""
        result = self.runner.invoke(cli.main)
        self.assertEqual(result.exit_code, 0)

    def test_version(self):
        """Test the version flag."""
        result = self.runner.invoke(cli.main, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(", version", result.output)

    def test_help(self):
        """Test the help flag."""
        result = self.runner.invoke(cli.main, ["--help"])
        self.assertEqual(result.exit_code, 0)

    def test_config(self):
        """Test that the config command exists. Should exit with no error."""
        result = self.runner.invoke(cli.main, ["config"])
        self.assertEqual(result.exit_code, 0)

    def test_experiment(self):
        """Test that the experiment command exists.
        Should exit with no error."""
        result = self.runner.invoke(cli.main, ["experiment"])
        self.assertEqual(result.exit_code, 0)

    def test_dataset(self):
        """Test that the dataset command exists. Should exit with no error."""
        result = self.runner.invoke(cli.main, ["dataset"])
        self.assertEqual(result.exit_code, 0)

    def test_status(self):
        """Test that the status command exists. Should exit with no error."""
        result = self.runner.invoke(cli.main, ["status"])
        self.assertEqual(result.exit_code, 0)

    def test_init(self):
        """Test that the init command exists. Should exit with error.
        Because no path is given b default."""
        result = self.runner.invoke(cli.main, ["init"])
        self.assertEqual(result.exit_code, 2)


# class CLIInitNotGitTest(unittest.TestCase):
# """Test the init subparser element of the CLI case when
# the path is not a git repository."""

# def setUp(self):
# self.cli = cli.QanatCli()
# self.init_subparser = self.cli.subparsers.choices["init"]

# @patch("builtins.input", return_value="n")
# def test_initpath_notgit_nocreate(self):
# """Test if cli exits when the user doen not want to
# create a git repository after being prompted."""
# with tempfile.TemporaryDirectory() as tmpdirname:
# with self.assertRaises(SystemExit):
# self.init_subparser.parse_args([tmpdirname])

# @patch("builtins.input", return_value="y")
# def test_initpath_notgit_create(self):
# """Test that the repertory is initialized as a git repository
# when the user wants to."""
# with tempfile.TemporaryDirectory() as tmpdirname:
# self.init_subparser.parse_args([tmpdirname])
# self.assertTrue(git.Repo(tmpdirname).git_dir)


# class CLIInitQanatDir(unittest.TestCase):
# """Test the init subparser element of the CLI for the existence/creation
# of the qanat directory."""

# def setUp(self):
# self.cli = cli.QanatCli()
# self.init_subparser = self.cli.subparsers.choices["init"]

# def test_initpath_qanatdir_notexist(self):
# """Test that the qanat directory is created when it does not exist."""
# with tempfile.TemporaryDirectory() as tmpdirname:
# self.init_subparser.parse_args([tmpdirname])
# self.assertTrue(os.path.isdir(os.path.join(tmpdirname, ".qanat")))

# def test_initpath_qanatdir_exist(self):
# """Test that nothing happens when the qanat directory already
# exists."""
# with tempfile.TemporaryDirectory() as tmpdirname:
# os.mkdir(os.path.join(tmpdirname, ".qanat"))
# self.init_subparser.parse_args([tmpdirname])
# self.assertTrue(os.path.isdir(os.path.join(tmpdirname, ".qanat")))
