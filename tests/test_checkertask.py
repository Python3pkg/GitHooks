"""Test :mod:`codechecker.checker.task`."""
import sys
import unittest
from shlex import split
from unittest import mock
from subprocess import (PIPE,
                        STDOUT)

from codechecker.checker.task import (Task as CheckerTask,
                                      CheckResult)
from codechecker.result_creators import (create_pylint_result,
                                         create_pyunittest_result)


class CheckerTestCase(unittest.TestCase):
    """Base test case of checker task.

    Contains methods which mocks Popen.
    """

    def setUp(self):
        self._prepare_shell_command()

    def assert_shell_command_executed(self, shell_command):
        """assert that shell command was executed once and was equal to passed one."""
        self.popen.assert_called_once_with(split(shell_command),
                                           stdout=PIPE, stderr=STDOUT)

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
    return code (which is default behavior of Task class).
    """

    def test_task_is_executable(self):
        """Executing task should create new process."""
        task = CheckerTask('taskname', 'command')

        task()
        self.assert_shell_command_executed('command')

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
        config = {'option': 'value'}

        task = CheckerTask('dummy', 'dummy', config)
        self.assertEqual('value', task.config['option'])


class BuildShellCommandTestCase(CheckerTestCase):
    def test_replace_options_placeholder_with_checker_options(self):
        """Pylint accepts pylintrc option."""
        command_pattern = 'pylint -f parseable /path/to/module.py ${options}'
        config = {
            'rcfile': 'pylintrc'
        }

        task = CheckerTask('dummy-taskname', command_pattern, config)
        task.command_options = {
            'rcfile': '--rcfile=${value}'
        }
        task()

        expected_command = 'pylint -f parseable /path/to/module.py ' \
            '--rcfile=pylintrc'
        self.assert_shell_command_executed(expected_command)

    def test_replace_options_placeholder_with_checker_options2(self):
        command_pattern = 'jshint ${options} /path/to/file.js'
        config = {
            'config': '.jshintrc'
        }

        task = CheckerTask('dummy-taskname', command_pattern, config)
        task.command_options = {
            'config': '--config ${value}'
        }
        task()

        expected_command = 'jshint --config .jshintrc /path/to/file.js'
        self.assert_shell_command_executed(expected_command)

    def test_config_options_should_be_properly_quoted(self):
        command_pattern = 'jshint ${options} /path/to/file.js'
        config = {
            'config': '.jshint rc'
        }

        task = CheckerTask('dummy-taskname', command_pattern, config)
        task.command_options = {
            'config': '--config ${value}'
        }
        task()

        expected_command = "jshint --config '.jshint rc' /path/to/file.js"
        self.assert_shell_command_executed(expected_command)


class CustomResultCreatorTestCase(CheckerTestCase):
    """Test :class:`codechecker.checker.task.Task`.

    This class test SUT in terms of determining result by custom result creator.
    Result creator is function which accepts Task object, shell return code,
    stdout and creates :class:`codechecker.checker.task.CheckResult`.
    """

    def test_pass_if_code_rate_is_10(self):
        """Test if result is determined by function assigned to result_creator attribute."""
        shell_output = _create_pylint_output(10)
        self._set_command_result(stdout=shell_output)
        taskname = 'pylint'

        task = _create_pylint_task(taskname=taskname)
        task.result_creator = create_pylint_result
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

        config = {'accepted-code-rate': 8}
        task = _create_pylint_task(taskname=dummy_taskname, config=config)
        task.result_creator = create_pylint_result
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
        task.result_creator = create_pylint_result
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
        task.result_creator = create_pyunittest_result
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
        task.result_creator = create_pyunittest_result
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
        config = {'accepted-code-rate': 9}
    return CheckerTask(taskname, command, config)


def _create_pylint_output(code_rate, messages=tuple()):
    lines = ['ignored stuff']
    lines.extend(messages)
    lines.append('ignored stuff')
    lines.append('Your code has been rated at {0:.2f}/10'.format(code_rate))
    return '\n'.join(lines)
