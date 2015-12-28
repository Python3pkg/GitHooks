"""Base checker classes.

Exports:

* :class:`CheckResult`: Result of checker execution
* :class:`Task`: Run checker and return result
"""
import sys
from collections import namedtuple
from subprocess import (Popen,
                        PIPE,
                        STDOUT)


_CheckResult = namedtuple('CheckResult', 'taskname status summary message')


class CheckResult(_CheckResult):
    """Describe result of checker execution.

    Contains result of :class:`codechecker.checker.task.Task` call.
    """

    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

    def __new__(cls, taskname, status=SUCCESS, summary=None, message=None):
        """Create CheckResult.

        Allows to pass default values to namedtuple.
        """
        return super(CheckResult, cls).__new__(
            cls, taskname, status, summary, message)

    def __repr__(self):
        """Convert object to readable format."""
        return '<CheckResult({}):{}, summary={}, message={}>'.format(
            self.taskname,
            self.status,
            repr(self.summary),
            repr(self.message)
        )


class Task:
    """Execute checker and return check result."""

    def __init__(self, taskname, command):
        """Set task name and command.

        :param taskname: Task name visible in checking result
        :type taskname: string
        :param command: Shell command
        :type command: string
        """
        self._taskname = taskname
        self._command = command

    def __call__(self):
        """Execute checker and return check result.

        :rtype: codechecker.checker.task.CheckResult
        """
        process = Popen(self._command, stdout=PIPE, stderr=STDOUT)
        stdout, _ = process.communicate()
        returncode = process.returncode

        if returncode == 0:
            return CheckResult(self._taskname)
        message = stdout.decode(sys.stdout.encoding)
        return CheckResult(self._taskname, CheckResult.ERROR, message=message)
