"""Test :mod:`codechecker.checker.task`."""
import sys
import unittest
import re
from unittest import mock
from subprocess import (PIPE,
                        STDOUT)

from codechecker.checker.task import (Task as CheckerTask,
                                      CheckResult,
                                      Config)
from codechecker.checker.task import InvalidConfigOptionError


class CheckerTestCase(unittest.TestCase):
    """Base test case of checker task.

    Contains methods which mocks Popen.
    """

    def setUp(self):
        self._prepare_shell_command()

    def _set_command_result(self, stdout='', returncode=0):
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

        self._set_command_result(stdout=errmsg, returncode=1)
        result = task()

        expected_result = CheckResult('taskname', CheckResult.ERROR,
                                      message=errmsg)
        _assert_checkresult_equal(expected_result, result)

    def test_task_accepts_config(self):
        config = [
            {'option': 'value'},
            Config({'option': 'value'})
        ]

        for each_config in config:
            task = CheckerTask('dummy-taskname', 'dummy-command', each_config)
            self.assertEqual('value', task.config.option)


class OutputCheckerTestCase(CheckerTestCase):
    """Test :class:`codechecker.checker.task.Task`.

    This class test SUT in terms of determining result based on shell command
    stdout/stderr.
    """

    def test_pass_if_code_rate_is_10(self):
        """Test if result is determined by function assigned to result_creator attribute."""
        shell_output = _create_pylint_output(10)
        self._set_command_result(stdout=shell_output)
        taskname = 'pylint'

        task = _create_pylint_task(taskname=taskname)
        task.result_creator = _pylint_result_creator
        result = task()

        expected_result = CheckResult(taskname)
        _assert_checkresult_equal(expected_result, result)

    def test_result_is_warning_if_code_rate_is_between_accepted_and_10(self):
        """Test if config is accessible by result_creator function."""
        dummy_taskname = 'pylint'
        messages = ('filename.py:1: first warning',
                    'filename.py:10: other warning')
        code_rate = 8.5
        shell_output = _create_pylint_output(code_rate, messages)
        self._set_command_result(stdout=shell_output)

        config = {'accepted_code_rate': 8}
        task = _create_pylint_task(taskname=dummy_taskname, config=config)
        task.result_creator = _pylint_result_creator
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.WARNING,
                                      'Code Rate 8.50/10',
                                      '\n'.join(messages))
        _assert_checkresult_equal(expected_result, result)


    def test_result_is_error_if_code_rate_is_below_accepted(self):
        dummy_taskname = 'pylint'
        messages = ('filename.py:1: first warning',
                    'filename.py:10: other warning')
        code_rate = 8
        shell_output = _create_pylint_output(code_rate, messages)
        self._set_command_result(stdout=shell_output)

        task = _create_pylint_task(taskname=dummy_taskname)
        task.result_creator = _pylint_result_creator
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.ERROR,
                                      'Failed: Code Rate 8.00/10',
                                      '\n'.join(messages))
        _assert_checkresult_equal(expected_result, result)


class UnittestCheckerTestCase(CheckerTestCase):

    def test_unittest_skipped_tests(self):
        dummy_taskname = 'unittest'
        lines = ('ignored line', 'Ran 26 tests in 0.263s', 'OK (skipped=1)')
        shell_output = '\n'.join(lines)
        self._set_command_result(stdout=shell_output)

        task = CheckerTask(dummy_taskname, 'dummy-command')
        task.result_creator = _create_python_unittest_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.WARNING,
                                      'Ran 26 tests in 0.263s - OK (skipped=1)')
        _assert_checkresult_equal(expected_result, result)

    def test_unittest_errors(self):
        dummy_taskname = 'unittest'
        lines = ('ignored line', 'FAILED (errors=2)')
        shell_output = '\n'.join(lines)
        self._set_command_result(stdout=shell_output, returncode=1)

        task = CheckerTask(dummy_taskname, 'dummy-command')
        task.result_creator = _create_python_unittest_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.ERROR,
                                      'FAILED (errors=2)')
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
    """Test :class:`codechecker.checker.task.Config`."""

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


def _create_pylint_task(taskname='dummy', command='dummy', config=None):
    if config is None:
        config = {'accepted_code_rate': 9}
    return CheckerTask(taskname, command, config)


def _create_pylint_output(code_rate, messages=tuple()):
    lines = ['ignored stuff']
    lines.extend(messages)
    lines.append('ignored stuff')
    lines.append('Your code has been rated at {0:.2f}/10'.format(code_rate))
    return '\n'.join(lines)


_RE_UNITTEST_SKIPPED_TESTS = re.compile(r'OK \(skipped=\d+\)')
_RE_UNITTEST_ERRORS = re.compile(
    r'FAILED \((?:failures=\d+)?(?:, )?(?:errors=\d+)?(?:, )?(?:skipped=\d+)?\)'
)
_RE_UNITTEST_TEST_NUMBER = re.compile(r'Ran \d+ tests in [0-9\.]+s')


def _create_python_unittest_result(task, returncode, shell_output):
    summary_match = _RE_UNITTEST_SKIPPED_TESTS.findall(shell_output)
    if not summary_match:
        summary_match = _RE_UNITTEST_ERRORS.findall(shell_output)

    ran_tests_match = _RE_UNITTEST_TEST_NUMBER.findall(shell_output)
    test_number_summary = ran_tests_match[0] + ' - ' if ran_tests_match else ''

    if returncode != 0:
        status = CheckResult.ERROR
        summary = summary_match[0] if summary_match else 'Errors'
    elif summary_match:
        status = CheckResult.WARNING
        summary = summary_match[0]
    else:
        status = CheckResult.SUCCESS
        summary = None
    return CheckResult(task.taskname, status, test_number_summary + summary)


_RE_CODE_RATE = re.compile(r'Your code has been rated at (-?[\d\.]+)/10')
_RE_PYLINT_MESSAGE = re.compile(
    r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)


def _pylint_result_creator(task, _, shell_output):
    accepted_code_rate = task.config.accepted_code_rate
    actual_code_rate = float(_RE_CODE_RATE.findall(shell_output)[0])
    if actual_code_rate == 10:
        return CheckResult(task.taskname)

    if actual_code_rate >= accepted_code_rate:
        status = CheckResult.WARNING
        summary = 'Code Rate {0:.2f}/10'.format(actual_code_rate)
    else:
        status = CheckResult.ERROR
        summary = 'Failed: Code Rate {0:.2f}/10'.format(actual_code_rate)
    messages = '\n'.join(_RE_PYLINT_MESSAGE.findall(shell_output))
    return CheckResult(task.taskname, status, summary, messages)
