"""Functions which create CheckResult objects."""
import re

from codechecker.checker.task import CheckResult


_RE_CODE_RATE = re.compile(r'Your code has been rated at (-?[\d\.]+)/10')
_RE_PYLINT_MESSAGE = re.compile(
    r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)


def create_pylint_result(task, _, shell_output) -> CheckResult:
    """Create check result for pylint checker."""
    accepted_code_rate = task.config['accepted-code-rate']
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


_RE_UNITTEST_SKIPPED_TESTS = re.compile(r'OK \(skipped=\d+\)')
_RE_UNITTEST_ERRORS = re.compile(
    r'FAILED \((?:failures=\d+)?(?:, )?'
    r'(?:errors=\d+)?(?:, )?(?:skipped=\d+)?\)'
)
_RE_UNITTEST_TEST_NUMBER = re.compile(r'Ran \d+ tests in [0-9\.]+s')


def create_pyunittest_result(task, returncode, shell_output) -> CheckResult:
    """Create python unittest checker result.

    In addition to unittest return code, this function checks if there are
    skipped tests. If skipped tests are found result has WARNING status.
    Also additional informations are displayed in summary
    (ran tests, skipped tests, errors, failures)
    """
    summary_match = _RE_UNITTEST_SKIPPED_TESTS.findall(shell_output)
    if not summary_match:
        summary_match = _RE_UNITTEST_ERRORS.findall(shell_output)

    ran_tests_match = _RE_UNITTEST_TEST_NUMBER.findall(shell_output)
    test_number_summary = \
        ran_tests_match[0] + ' - ' if ran_tests_match else ''

    message = None
    if returncode != 0:
        status = CheckResult.ERROR
        summary = test_number_summary + (summary_match[0]
                                         if summary_match else 'Failed')
        message = shell_output
    elif summary_match:
        status = CheckResult.WARNING
        summary = test_number_summary + summary_match[0]
    else:
        status = CheckResult.SUCCESS
        summary = test_number_summary + 'OK'
    return CheckResult(task.taskname, status, summary, message)


_RE_PHPUNIT_RESOURCES = re.compile(
    r'^Time: \d+ ms, Memory: [0-9\.]+(?:Mb|Gb)$',
    re.MULTILINE
)
_RE_PHPUNIT_SKIPPED_TESTS = re.compile(
    r'^OK, but incomplete, skipped, or risky tests!$',
    re.MULTILINE
)
_RE_PHPUNIT_SUMMARY = re.compile(
    r'^Tests: \d+, Assertions: \d+.+$',
    re.MULTILINE
)


def create_phpunit_result(task, returncode, stdout) -> CheckResult:
    """Create python unittest checker result.

    In addition to return code, this function checks if there are
    skipped tests. If skipped tests are found result has WARNING status.
    Also additional informations are displayed in summary
    (ran tests, skipped tests, errors, failures, resources)
    """
    skipped_tests_match = _RE_PHPUNIT_SKIPPED_TESTS.findall(stdout)
    summary_match = _RE_PHPUNIT_SUMMARY.findall(stdout)
    resources_match = _RE_PHPUNIT_RESOURCES.findall(stdout)

    summary = resources_match[0] + ' - ' + summary_match[0]
    message = None
    if returncode != 0:
        status = CheckResult.ERROR
        message = stdout
    elif skipped_tests_match:
        status = CheckResult.WARNING
    else:
        status = CheckResult.SUCCESS
    return CheckResult(task.taskname, status, summary, message)
