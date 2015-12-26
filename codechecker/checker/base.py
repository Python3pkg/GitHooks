"""Checkers module.

This module contains functions and classes doing pre-commit checks
(checkers) and :py:class:`CheckResult` class. Checker must be callable and
return :py:class:`CheckResult` object.
"""
import sys
import re
from subprocess import Popen, PIPE
from shlex import split
from collections import namedtuple
from enum import Enum


_CheckResult = namedtuple('CheckResult', 'taskname status summary message')


class CheckResult(_CheckResult):
    """Checker task result status."""

    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'


class PylintChecker:
    """Checks pylint code rate.

    Checks file passed to constructor. Result is success if code has been rated
    at least as high as accepted_code_rate constructor argument is.
    """

    RE_CODE_RATE = re.compile(r'Your code has been rated at (-?[\d\.]+)/10')
    RE_PYLINT_MESSAGE = re.compile(
        r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)

    def __init__(self, filename, abspath, accepted_code_rate):
        """Set file path and accepted code rate.

        :param filename: path to file relative to git repository root
        :type filename: string
        :param accepted_code_rate: minimal accepted code rate
        :type accepted_code_rate: integer or float
        """
        self.abspath = abspath
        self.file_name = filename
        self.accepted_code_rate = accepted_code_rate
        self.rcfile = None

    def __call__(self):
        """Run checker and return result informations."""
        pylint_args = split(self.get_command())
        pylint_process = Popen(pylint_args, stdout=PIPE, stderr=PIPE)
        pylint_process.wait()
        pylint_output = pylint_process.stdout.read()\
            .decode(sys.stdout.encoding)

        current_rate = float(self.RE_CODE_RATE.findall(pylint_output)[0])

        if current_rate == 10:
            return _create_checkresult(self.get_taskname())

        messages = '\n'.join(self.RE_PYLINT_MESSAGE.findall(pylint_output))
        if current_rate >= self.accepted_code_rate:
            status = CheckResult.WARNING
            summary = 'Code Rate {}/10'.format(current_rate)
        else:
            status = CheckResult.ERROR
            summary = 'Failed: Code Rate {}/10'.format(current_rate)

        return _create_checkresult(
            self.get_taskname(), status, summary, messages)

    def get_command(self):
        """Get command line command."""
        options = []
        if self.rcfile:
            options.append('--rcfile={}'.format(self.rcfile))
        return 'pylint -f parseable {abspath} {options}'.format(
            abspath=self.abspath,
            options=' '.join(options)
        )

    def get_taskname(self):
        """Get task name."""
        return 'Pylint {}:'.format(self.file_name)

    def __repr__(self):
        """Show debug info."""
        return '<PylintChecker file={}, accepted_code_rate={}, abspath={}>'\
            .format(
                repr(self.file_name),
                repr(self.accepted_code_rate),
                repr(self.abspath)
            )


class ExitCodeChecker:
    """Fail if command exits with error code.

    Fail if command passed to constructor exits with non 0 return code.
    """

    def __init__(self, command, task_name):
        """Set command and task name.

        :param command: system shell command
        :type command: string
        :param task_name: Task name describing result in console
        :type task_name: string
        """
        self._command = command
        self._task_name = task_name

    def __call__(self):
        """Run checker and return result informations."""
        args = split(self._command)
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        returncode = process.wait()

        if not returncode:
            return _create_checkresult(self._task_name)

        status = CheckResult.ERROR
        message = process.stdout.read().decode(sys.stdout.encoding)
        message += process.stderr.read().decode(sys.stderr.encoding)

        return _create_checkresult(self._task_name, status, message=message)

    def __repr__(self):
        """Show debug info."""
        return '<ExitCodeChecker: command={}, task_name={}>'.format(
            repr(self._command),
            repr(self._task_name)
        )


def _create_checkresult(
        taskname, status=CheckResult.SUCCESS, summary='', message=''):
    """Create :class:`CheckResult`.

    Usefull when trying to create :class:`CheckResult` with default values
    """
    return CheckResult(taskname, status, summary, message)
