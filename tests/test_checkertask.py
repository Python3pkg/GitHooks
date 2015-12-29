"""Test :mod:`codechecker.checker.task`."""
import sys
import unittest
import re
from unittest import mock
from subprocess import (PIPE,
                        STDOUT)

from codechecker.checker.task import (Task as CheckerTask,
                                      CheckResult,
                                      Config,
                                      InvalidConfigOptionError)


class CheckerTestCase(unittest.TestCase):
    """Base test case of checker task.

    Contains methods which mocks Popen.
    """

    def setUp(self):
        self._prepare_shell_command()

    def _set_command_result(self, output='', returncode=0):
        """Set shell command stdout/stderr and return code."""
        stdout = output.encode(sys.stdout.encoding) # convert string to bytes
        self.popen.return_value.communicate.return_value = (stdout, b'')
        self.popen.return_value.returncode = returncode

    def _prepare_shell_command(self):
        """Mock Popen."""
        popen_patcher = mock.patch('codechecker.checker.task.Popen',
                                   autospec=True)
        self.addCleanup(popen_patcher.stop)
        self.popen = popen_patcher.start()
        self._set_command_result()


class ExitCodeCheckerTestCase(CheckerTestCase):
    """Test :class:`codechecker.checker.task.Task`.

    Test if :class:`codechecker.checker.task.Task` executes correct shell
    commands and returns correct results.

    This class test SUT in terms of determining result based on shell command
    return code.
    """

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


class OutputCheckerTestCase(CheckerTestCase):
    """Test :class:`codechecker.checker.task.Task`.

    This class test SUT in terms of determining result based on shell command
    stdout/stderr.
    """

    def test_pass_if_code_rate_is_10(self):
        shell_output = _create_pylint_output(10)
        self._set_command_result(shell_output)
        taskname = 'pylint'

        task = CheckerTask(taskname, 'command-not-important-here')
        task.result_creator = _pylint_result_creator
        result = task()

        expected_result = CheckResult(taskname)
        _assert_checkresult_equal(expected_result, result)


    def test_result_is_error_if_code_rate_is_below_accepted(self):
        taskname = 'pylint'
        messages = ('filename.py:1: first warning',
                    'filename.py:10: other warning')
        code_rate = 8
        shell_output = _create_pylint_output(code_rate, messages)
        self._set_command_result(shell_output)

        task = CheckerTask(taskname, 'command-not-important-here')
        task.result_creator = _pylint_result_creator
        result = task()

        expected_result = CheckResult(taskname,
                                      CheckResult.ERROR,
                                      'Failed: Code Rate 8.00/10',
                                      '\n'.join(messages))
        _assert_checkresult_equal(expected_result, result)


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


class ConfigTestCase(unittest.TestCase):
    def test_access_properties_by_object_notation(self):
        conf = Config({
            'option1': 'value1',
            'option2': 'value'
        })
        conf.option2 = 'value2'

        self.assertEqual('value1', conf.option1)
        self.assertEqual('value2', conf.option2)

    def test_throws_InvalidConfigOption_if_undefined_option_is_accessed(self):
        conf = Config({
            'option': 'value'
        })

        self.assertRaises(InvalidConfigOptionError, lambda: conf.invalid_option)
        with self.assertRaises(InvalidConfigOptionError):
            conf.invalid_option = 'value'

    def test_contains(self):
        conf = Config({
            'option': 'value'
        })

        self.assertIn('option', conf)
        self.assertNotIn('invalid-option', conf)

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


def _create_pylint_output(code_rate, messages=tuple()):
    lines = ['ignored stuff']
    lines.extend(messages)
    lines.append('ignored stuff')
    lines.append('Your code has been rated at {0:.2f}/10'.format(code_rate))
    return '\n'.join(lines)


_RE_CODE_RATE = re.compile(r'Your code has been rated at (-?[\d\.]+)/10')
_RE_PYLINT_MESSAGE = re.compile(
    r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)


def _pylint_result_creator(task, _, shell_output):
    accepted_code_rate = 9
    actual_code_rate = float(_RE_CODE_RATE.findall(shell_output)[0])
    if actual_code_rate == 10:
        return CheckResult(task.taskname)

    if actual_code_rate >= accepted_code_rate:
        status = CheckResult.WARNING
        summary = 'Code Rate {}/10'.format(actual_code_rate)
    else:
        status = CheckResult.ERROR
        summary = 'Failed: Code Rate {0:.2f}/10'.format(actual_code_rate)
    messages = '\n'.join(_RE_PYLINT_MESSAGE.findall(shell_output))
    return CheckResult(task.taskname, status, summary, messages)
