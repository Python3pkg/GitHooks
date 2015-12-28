"""Test :mod:`codechecker.checker.task`."""
import sys
import unittest
from unittest import mock
from subprocess import (PIPE,
                        STDOUT)

from codechecker.checker.task import Task as CheckerTask
from codechecker.checker.task import CheckResult

class CheckerTaskTestCase(unittest.TestCase):
    """Test :class:`codechecker.checker.task.Task`.

    Test if :class:`codechecker.checker.task.Task` executes correct shell
    commands and returns correct results.
    """

    def setUp(self):
        self._prepare_shell_command()

    def test_task_is_executable(self):
        """Executing task should create new process."""
        task = CheckerTask('taskname', 'command')

        task()
        self.popen.assert_called_once_with('command',
                                           stdout=PIPE, stderr=STDOUT)

    def test_task_returns_CheckResult(self):
        """Checker task should return :class:`codechecker.checker.task.CheckResult`"""
        # pylint: disable=no-self-use
        task = CheckerTask('taskname', 'command')
        result = task()
        expected_result = CheckResult('taskname')
        _assert_checkresult_equal(expected_result, result)

    def test_CheckResult_has_error_status_if_command_fails(self):
        """Task should fail if command exits with non zero status"""
        task = CheckerTask('taskname', 'command')
        errmsg = 'error message'

        self._set_command_result(output=errmsg, returncode=1)
        result = task()

        expected_result = CheckResult('taskname', CheckResult.ERROR,
                                      message=errmsg)
        _assert_checkresult_equal(expected_result, result)

    def _set_command_result(self, output='', returncode=0):
        stdout = output.encode(sys.stdout.encoding)
        self.popen.return_value.communicate.return_value = (stdout, b'')
        self.popen.return_value.returncode = returncode

    def _prepare_shell_command(self):
        popen_patcher = mock.patch('codechecker.checker.task.Popen',
                                   autospec=True)
        self.addCleanup(popen_patcher.stop)
        self.popen = popen_patcher.start()
        self._set_command_result()


class CheckResultTestCase(unittest.TestCase):
    """Test :class:`codechecker.checker.task.CheckResult`.
    
    Test if :class:`codechecker.checker.task.CheckResult` handles correct
    informations.
    """

    def test_default_values(self):
        """Test :class:`codechecker.checker.task.CheckResult` default values."""
        # pylint: disable=no-self-use
        checker_result = CheckResult('taskname')
        expected_checker_result = CheckResult(
            'taskname',
            status=CheckResult.SUCCESS,
            summary=None,
            message=None
        )
        _assert_checkresult_equal(expected_checker_result, checker_result)


def _assert_checkresult_equal(first, second):
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
