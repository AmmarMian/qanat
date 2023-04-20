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
        args = self.cli.main_parser.parse_args(['init', 'path'])
        self.assertEqual(args.command, 'init')

        args = self.cli.main_parser.parse_args(['status'])
        self.assertEqual(args.command, 'status')

    def test_version(self):
        """Test the version flag."""
        with self.assertRaises(SystemExit):
            self.cli.main_parser.parse_args(['--version'])

    def test_help(self):
        """Test the help flag."""
        with self.assertRaises(SystemExit):
            self.cli.main_parser.parse_args(['--help'])
