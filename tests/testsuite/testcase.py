"""Base test case for tests using mocked Popen."""

import sys
import unittest
from unittest import mock
from shlex import split
from subprocess import (PIPE,
                        STDOUT)

from codechecker.checker.task import CheckResult


class ShellTestCase(unittest.TestCase):
    """Base test case of checker task.

    Contains methods which mocks Popen.
    """

    def setUp(self):
        self._prepare_shell_command()

    def assert_shell_command_executed(self, shell_command):
        """assert that shell command was executed once and was equal to passed one."""
        self.popen.assert_called_once_with(split(shell_command),
                                           stdout=PIPE, stderr=STDOUT)

    def patch_shellcommand_result(self, stdout='', returncode=0):
        """Set shell command stdout/stderr and return code."""
        # communicate return tuple of bytes so convert string to bytes
        stdout_bytes = stdout.encode(sys.stdout.encoding)
        self.popen.return_value.communicate.return_value = (stdout_bytes, b'')
        self.popen.return_value.returncode = returncode

    def _prepare_shell_command(self):
        """Mock Popen."""
        popen_patcher = mock.patch('codechecker.checker.task.Popen',
                                   autospec=True)
        self.addCleanup(popen_patcher.stop)
        self.popen = popen_patcher.start()
        self.patch_shellcommand_result()


def assert_checkresult_equal(first, second):
    """Check equality of :class:`codechekcer.checker.task.CheckResult`.

    Check if two passed arguments are
    :class:`codechekcer.checker.task.CheckResult` and if all their attributes
    are equal.
    """
    isequal = isinstance(first, CheckResult) and \
        isinstance(second, CheckResult) and \
        first.taskname == second.taskname and \
        first.status == second.status and \
        first.summary == second.summary and \
        first.message == second.message
    if not isequal:
        raise AssertionError('Assertion Error {} != {}'.format(
            repr(first),
            repr(second)
        ))
