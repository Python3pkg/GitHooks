"""This package contains functions and classes doing pre-commit checks (checkers)
and :py:class:`CheckResult` class. Checker must be callable and return 
:py:class:`CheckResult` object.
"""
import sys
import re
from subprocess import Popen, PIPE

class CheckResult:
    """Contains result of single pre-commit check"""

    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'

    def __init__(self, task_name, status=SUCCESS):
        self.task_name = task_name
        self.status = status
        self.summary = ''
        self.info = ''
        self.message = ''

    def __repr__(self):
        return '{self.task_name}, {self.status}, {self.summary}, {self.info}, {self.message}'.format(self=self)

def check_unittest():
    """Check if unittest passes

    :rtype: CheckResult
    """
    test_args = 'python3 -m unittest discover .'.split()
    test_process = Popen(test_args, stdout=PIPE, stderr=PIPE)
    test_process.wait()
    tests_output = test_process.stderr.read().decode(sys.stdout.encoding)

    result = CheckResult('Running python unittest')
    if not tests_output.endswith('OK\n'):
        result.status = CheckResult.ERROR
        result.message = tests_output
    return result


class PylintCheck:
    """Checks pylint code rate

    Checks file passed to constructor. Result is success if code has been rated
    at least as high as PylintCheck.ACCEPTED_PYLINT_RATE is.
    """
    ACCEPTED_PYLINT_RATE = 9
    RE_CODE_RATE = re.compile(r'Your code has been rated at ([\d\.]+)/10')
    RE_PYLINT_MESSAGE = re.compile(r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)

    def __init__(self, file_name):
        self.file_name = file_name

    def __call__(self):
        pylint_args = 'pylint -f parseable {}'.format(self.file_name).split()
        pylint_process = Popen(pylint_args, stdout=PIPE, stderr=PIPE)
        pylint_process.wait()
        pylint_output = pylint_process.stdout.read().decode(sys.stdout.encoding)

        current_rate = float(self.RE_CODE_RATE.findall(pylint_output)[0])

        result = CheckResult('Checking file {} by pylint'.format(self.file_name))

        if current_rate == 10:
            return result

        messages = '\n'.join(self.RE_PYLINT_MESSAGE.findall(pylint_output))
        if current_rate >= self.ACCEPTED_PYLINT_RATE:
            result.status = CheckResult.WARNING
            result.summary = 'Code Rate {}/10'.format(current_rate)
        else:
            result.status = CheckResult.ERROR
            result.summary = 'Failed: Code Rate {}/10'.format(current_rate)
        result.message = messages

        return result
