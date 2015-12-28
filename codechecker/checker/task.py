"""Base checker classes.

Exports:

* :class:`CheckResult`: Result of checker execution
* :class:`ExitCodeChecker`: Run checker and return result
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
        return super(CheckResult, cls).__new__(cls, taskname, status,
                                               summary, message)

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

    # pylint: disable=too-few-public-methods
    def __init__(self, taskname, command, result_creator=None):
        """Set task name and command.

        :param taskname: Task name visible in checking result
        :type taskname: string
        :param command: Shell command
        :type command: string
        """
        self.taskname = taskname
        self._command = command
        if result_creator is None:
            self._create_result = _create_result_by_returncode
        else:
            self._create_result = result_creator

    def __call__(self):
        """Execute checker and return check result.

        :rtype: codechecker.checker.task.CheckResult
        """
        returncode, stdout = self._execute_shell_command()
        return self._create_result(self, returncode, stdout)

    def _execute_shell_command(self):
        """Execute shell command and return result.

        Execute shell command and return its return code, stdout and stderr.
        Command stderr is redirected to stdout.

        :returns: first item is return code(int), second stdout and stderr(str)
        :rtype: tuple
        """
        process = Popen(self._command, stdout=PIPE, stderr=STDOUT)
        stdout, _ = process.communicate()
        returncode = process.returncode
        return returncode, stdout.decode(sys.stdout.encoding)


def _create_result_by_returncode(task, returncode, shell_output):
    """Create CheckResult based on shell returncode."""
    if returncode == 0:
        return CheckResult(task.taskname)
    return CheckResult(task.taskname, CheckResult.ERROR, message=shell_output)
