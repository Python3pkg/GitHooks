"""Test result creators."""
from codechecker.result_creators import (create_pylint_result,
                                         create_pyunittest_result,
                                         create_phpunit_result)
from codechecker.checker.task import (Task,
                                      CheckResult)
from tests.testsuite.testcase import (ShellTestCase,
                                      assert_checkresult_equal)


class PylintResultCreatorTestCase(ShellTestCase):
    """Test :class:`codechecker.checker.task.Task`.

    This class test SUT in terms of determining result by custom result creator.
    Result creator is function which accepts Task object, shell return code,
    stdout and creates :class:`codechecker.checker.task.CheckResult`.
    """

    def test_pass_if_code_rate_is_10(self):
        """Test if result is determined by function assigned to result_creator attribute."""
        shell_output = create_pylint_output(10)
        self.patch_shellcommand_result(stdout=shell_output)
        taskname = 'pylint'

        task = create_pylint_task(taskname=taskname)
        task.result_creator = create_pylint_result
        result = task()

        expected_result = CheckResult(taskname)
        assert_checkresult_equal(expected_result, result)

    def test_result_is_warning_if_code_rate_is_between_accepted_and_10(self):
        """Test if config is accessible by result_creator function."""
        dummy_taskname = 'pylint'
        messages = ('filename.py:1: first warning',
                    'filename.py:10: other warning')
        code_rate = 8.5
        shell_output = create_pylint_output(code_rate, messages)
        self.patch_shellcommand_result(stdout=shell_output)

        config = {'accepted-code-rate': 8}
        task = create_pylint_task(taskname=dummy_taskname, config=config)
        task.result_creator = create_pylint_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.WARNING,
                                      'Code Rate 8.50/10',
                                      '\n'.join(messages))
        assert_checkresult_equal(expected_result, result)


    def test_result_is_error_if_code_rate_is_below_accepted(self):
        dummy_taskname = 'pylint'
        messages = ('filename.py:1: first warning',
                    'filename.py:10: other warning')
        code_rate = 8
        shell_output = create_pylint_output(code_rate, messages)
        self.patch_shellcommand_result(stdout=shell_output)

        task = create_pylint_task(taskname=dummy_taskname)
        task.result_creator = create_pylint_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.ERROR,
                                      'Failed: Code Rate 8.00/10',
                                      '\n'.join(messages))
        assert_checkresult_equal(expected_result, result)

    def test_result_is_warning_if_code_rate_is_not_returned_by_pylint(self):
        dummy_taskname = 'pylint'
        messages = ('filename.py:1: first warning',
                    'filename.py:10: other warning')
        shell_output = '\n'.join(messages)
        self.patch_shellcommand_result(stdout=shell_output)

        task = create_pylint_task(taskname=dummy_taskname)
        task.result_creator = create_pylint_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.WARNING,
                                      'Code Rate UNKNOWN',
                                      '\n'.join(messages))
        assert_checkresult_equal(expected_result, result)


class PythonUnittestResultCreatorTestCase(ShellTestCase):

    def test_unittest_skipped_tests(self):
        dummy_taskname = 'unittest'
        lines = ('ignored line', 'Ran 26 tests in 0.263s', 'OK (skipped=1)')
        shell_output = '\n'.join(lines)
        self.patch_shellcommand_result(stdout=shell_output)

        task = Task(dummy_taskname, 'dummy-command')
        task.result_creator = create_pyunittest_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.WARNING,
                                      'Ran 26 tests in 0.263s - OK (skipped=1)')
        assert_checkresult_equal(expected_result, result)

    def test_unittest_errors(self):
        dummy_taskname = 'unittest'
        lines = ('ignored line', 'FAILED (errors=2)')
        shell_output = '\n'.join(lines)
        self.patch_shellcommand_result(stdout=shell_output, returncode=1)

        task = Task(dummy_taskname, 'dummy-command')
        task.result_creator = create_pyunittest_result
        result = task()

        expected_result = CheckResult(dummy_taskname,
                                      CheckResult.ERROR,
                                      'FAILED (errors=2)',
                                      shell_output)
        assert_checkresult_equal(expected_result, result)


class PHPUnitResultCreatorTestCase(ShellTestCase):
    def test_ok(self):
        dummy_taskname = 'phpunit'
        resource_summary = 'Time: 60 ms, Memory: 3.75Mb'
        ran_tests_summary = 'OK (40 tests, 57 assertions)'
        lines = ('dummy', resource_summary, ran_tests_summary)
        stdout = '\n'.join(lines)
        self.patch_shellcommand_result(stdout=stdout)

        task = Task(dummy_taskname, 'dummy-command')
        task.result_creator = create_phpunit_result
        result = task()

        expected_result = CheckResult(
            dummy_taskname,
            CheckResult.SUCCESS,
            'OK (40 tests, 57 assertions) - Time: 60 ms, Memory: 3.75Mb'
        )
        assert_checkresult_equal(expected_result, result)

    def test_skipped_tests(self):
        dummy_taskname = 'phpunit'
        resource_summary = 'Time: 60 ms, Memory: 3.75Mb'
        ran_tests_summary = 'OK, but incomplete, skipped, or risky tests!'
        lines = ('dummy', resource_summary, ran_tests_summary)
        stdout = '\n'.join(lines)
        self.patch_shellcommand_result(stdout=stdout)

        task = Task(dummy_taskname, 'dummy-command')
        task.result_creator = create_phpunit_result
        result = task()

        expected_result = CheckResult(
            dummy_taskname,
            CheckResult.WARNING,
            'OK, but incomplete, skipped, or risky tests!' \
            ' - Time: 60 ms, Memory: 3.75Mb'
        )
        assert_checkresult_equal(expected_result, result)

    def test_failure(self):
        dummy_taskname = 'phpunit'
        resource_summary = 'Time: 60 ms, Memory: 3.75Mb'
        ran_tests_summary = 'Tests: 40, Assertions: 55, ' \
            'Failures: 1, Incomplete: 1.'
        lines = ('dummy', resource_summary, ran_tests_summary)
        stdout = '\n'.join(lines)
        self.patch_shellcommand_result(stdout=stdout, returncode=1)

        task = Task(dummy_taskname, 'dummy-command')
        task.result_creator = create_phpunit_result
        result = task()

        expected_result = CheckResult(
            dummy_taskname,
            CheckResult.ERROR,
            ran_tests_summary + ' - Time: 60 ms, Memory: 3.75Mb',
            message=stdout
        )
        assert_checkresult_equal(expected_result, result)

    def test_php_fatalerror(self):
        dummy_taskname = 'phpunit'
        lines = ('dummy', 'PHP Fatal error:  Error description ..')
        stdout = '\n'.join(lines)
        self.patch_shellcommand_result(stdout=stdout, returncode=1)

        task = Task(dummy_taskname, 'dummy-command')
        task.result_creator = create_phpunit_result
        result = task()

        expected_result = CheckResult(
            dummy_taskname,
            CheckResult.ERROR,
            'FAILED',
            message=stdout
        )
        assert_checkresult_equal(expected_result, result)


def create_pylint_task(taskname='dummy', command='dummy', config=None):
    """Create Task.

    Default config argument contains accepted-code-rate option.
    """
    if config is None:
        config = {'accepted-code-rate': 9}
    return Task(taskname, command, config)


def create_pylint_output(code_rate, messages=tuple()):
    """Create fake pylint command output."""
    lines = ['ignored stuff']
    lines.extend(messages)
    lines.append('ignored stuff')
    lines.append('Your code has been rated at {0:.2f}/10'.format(code_rate))
    return '\n'.join(lines)
