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
