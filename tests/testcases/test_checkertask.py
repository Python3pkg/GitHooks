"""Test :mod:`codechecker.checker.task`."""
import unittest

from codechecker.checker.task import (Task as CheckerTask,
                                      CheckResult)
from tests.testcases.testcase import (ShellTestCase,
                                      assert_checkresult_equal)


class ExitCodeCheckerTestCase(ShellTestCase):
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
        assert_checkresult_equal(expected_result, result)

    def test_CheckResult_has_error_status_if_command_fails(self):
        """Task should fail if command exits with non zero status"""
        task = CheckerTask('taskname', 'command')
        errmsg = 'error message'

        self.patch_shellcommand_result(stdout=errmsg, returncode=1)
        result = task()

        expected_result = CheckResult('taskname', CheckResult.ERROR,
                                      message=errmsg)
        assert_checkresult_equal(expected_result, result)

    def test_task_accepts_config(self):
        config = {'option': 'value'}

        task = CheckerTask('dummy', 'dummy', config)
        self.assertEqual('value', task.config['option'])


class BuildShellCommandTestCase(ShellTestCase):
    """Test if Task class properly builds shell command."""

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

    def test_shell_executable_can_be_configured(self):
        command_pattern = '${executable} ${options}'
        config = {
            'executable': 'path/to/phpunit'
        }

        task = CheckerTask('dummy', command_pattern, config)
        task()

        expected_command = 'path/to/phpunit'
        self.assert_shell_command_executed(expected_command)

    def test_empty_string_is_valid_command_option(self):
        command_pattern = 'command ${options}'
        config = {
            'config': ''
        }

        task = CheckerTask('dummy', command_pattern, config)
        task.command_options = {
            'config': '--config ${value}'
        }
        task()

        expected_command = "command --config ''"
        self.assert_shell_command_executed(expected_command)

    def test_command_options_can_be_passed_directly_to_command_pattern(self):
        command_pattern = 'command ${opt1} ${opt2}'
        config = {
            'opt1': 'val1',
            'opt2': 'val2'
        }

        task = CheckerTask('dummy', command_pattern, config)
        task.command_options = {
            'opt1': '--opt1 ${value}',
            'opt2': '${value}'
        }
        task()

        expected_command = 'command --opt1 val1 val2'
        self.assert_shell_command_executed(expected_command)

    def test_option_is_not_passed_to_command_if_its_config_option_is_none(self):
        command_pattern = 'command ${opt}'
        config = {
            'opt': None
        }

        task = CheckerTask('dummy', command_pattern, config)
        task.command_options = {
            'opt': '--opt1 ${value}'
        }
        task()

        expected_command = 'command'
        self.assert_shell_command_executed(expected_command)

    def test_option_is_not_passed_to_command_if_its_config_option_is_none2(self):
        command_pattern = 'command ${options}'
        config = {
            'opt': None
        }

        task = CheckerTask('dummy', command_pattern, config)
        task.command_options = {
            'opt': '--opt1 ${value}'
        }
        task()

        expected_command = 'command'
        self.assert_shell_command_executed(expected_command)


class CustomResultCreatorTestCase(ShellTestCase):
    """Test Task class properly uses custom result creator.

    Result creator is function which accepts Task object, shell return code,
    stdout and creates :class:`codechecker.checker.task.CheckResult`.
    """

    def test_pass_if_code_rate_is_10(self):
        """Test if result is determined by function assigned to result_creator attribute."""
        expected_summary = 'expected summary'
        def result_creator(task, *_):
            return CheckResult(task.taskname, summary=expected_summary)
        self.patch_shellcommand_result(stdout='dummy')
        taskname = 'dummy'

        task = CheckerTask(taskname, 'dummy-command')
        task.result_creator = result_creator
        result = task()

        expected_result = CheckResult(taskname, summary=expected_summary)
        assert_checkresult_equal(expected_result, result)


class CheckResultTestCase(unittest.TestCase):
    """Test CheckResult default values.

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
        assert_checkresult_equal(expected_checker_result, checker_result)
