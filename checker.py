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


class _SingleFileChecker:
    """Base class for checkers which checks single file"""

    def __init__(self, file_name):
        """Set file to be checked

        :param file_name: path to file
        :type file_name: string
        """
        self.file_name = file_name


class PylintChecker(_SingleFileChecker):
    """Checks pylint code rate

    Checks file passed to constructor. Result is success if code has been rated
    at least as high as accepted_code_rate constructor argument is.
    """

    RE_CODE_RATE = re.compile(r'Your code has been rated at ([\d\.]+)/10')
    RE_PYLINT_MESSAGE = re.compile(r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)
    
    def __init__(self, file_name, accepted_code_rate):
        """Set file path and accepted code rate

        :param accepted_code_rate: minimal accepted code rate
        :type accepted_code_rate: integer or float
        """
        super(PylintChecker, self).__init__(file_name)
        self.accepted_code_rate = accepted_code_rate

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
        if current_rate >= self.accepted_code_rate:
            result.status = CheckResult.WARNING
            result.summary = 'Code Rate {}/10'.format(current_rate)
        else:
            result.status = CheckResult.ERROR
            result.summary = 'Failed: Code Rate {}/10'.format(current_rate)
        # Include pylint messages to result
        result.message = messages

        return result


class PEP8Checker(_SingleFileChecker):
    "Checks PEP8 compliance"

    def __call__(self):
        pep8_args = 'pep8 {}'.format(self.file_name).split()
        pep8_process = Popen(pep8_args, stdout=PIPE, stderr=PIPE)
        pep8_process.wait()
        output = pep8_process.stdout.read().decode(sys.stdout.encoding)

        result = CheckResult('PEP8 compliance for {}'.format(self.file_name))
        if output:
            result.status = CheckResult.ERROR
            result.message = output
        return result
