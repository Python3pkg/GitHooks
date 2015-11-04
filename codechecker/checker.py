"""Checkers module

This module contains functions and classes doing pre-commit checks
(checkers) and :py:class:`CheckResult` class. Checker must be callable and
return :py:class:`CheckResult` object.
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

    RE_CODE_RATE = re.compile(r'Your code has been rated at (-?[\d\.]+)/10')
    RE_PYLINT_MESSAGE = re.compile(
        r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)

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
        pylint_output = pylint_process.stdout.read()\
            .decode(sys.stdout.encoding)

        current_rate = float(self.RE_CODE_RATE.findall(pylint_output)[0])

        result = CheckResult(
            'Checking file {} by pylint'.format(self.file_name))

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


class ExitCodeChecker:
    """Fail if command exits with error code

    Fail if command passed to constructor exits with non 0 return code.
    """

    def __init__(self, command, task_name):
        """Set command and task name

        :param command: system shell command
        :type command: string
        :param task_name: Task name describing result in console
        :type task_name: string
        """
        self._command = command
        self._task_name = task_name

    def __call__(self):
        args = self._command.split()
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        result = CheckResult(self._task_name)
        if returncode:
            result.status = CheckResult.ERROR
            result.message = process.stdout.read().decode(sys.stdout.encoding)
            result.message += process.stderr.read().decode(sys.stderr.encoding)
        return result
