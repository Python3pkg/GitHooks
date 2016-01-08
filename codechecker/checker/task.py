"""Base checker classes.

Exports:

* :class:`CheckResult`: Result of checker execution.
* :class:`Task`: Run checker and return result.
* :class:`Config`: Handle task configuration.
"""
import sys
from string import Template
from shlex import (split,
                   quote)
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
    # pylint: disable=too-few-public-methods
    """Execute checker and return check result."""

    def __init__(self, taskname, command, config=None):
        """Set task name and command.

        :param taskname: Task name visible in checking result
        :type taskname: string
        :param command: Shell command
        :type command: string
        """
        self.taskname = taskname
        self._command = Template(command)
        if config is None:
            self.config = {}
        else:
            self.config = config
        self.result_creator = create_result_by_returncode
        self.command_options = {}

    def __call__(self):
        """Execute checker and return check result.

        :rtype: codechecker.checker.task.CheckResult
        """
        returncode, stdout = self._execute_shell_command()
        return self.result_creator(self, returncode, stdout)

    def __repr__(self):
        """Create representation of Task."""
        return '<Task({}): command={}, config={}>'.format(
            self.taskname,
            repr(' '.join([quote(opt) for opt in self._build_command()])),
            repr(self.config)
        )

    def _execute_shell_command(self):
        """Execute shell command and return result.

        Execute shell command and return its return code, stdout and stderr.
        Command stderr is redirected to stdout.

        :returns: first item is return code(int), second stdout and stderr(str)
        :rtype: tuple
        """
        process = Popen(self._build_command(), stdout=PIPE, stderr=STDOUT)
        stdout, _ = process.communicate()
        returncode = process.returncode
        return returncode, stdout.decode(sys.stdout.encoding)

    def _build_command(self):
        """Prepare shell command.

        Passes some config options to command options.
        """
        options = []
        for each_option in self.command_options:
            option_value = self.config[each_option]
            if option_value is None:
                continue
            option_pattern = Template(
                self.command_options[each_option]
            )
            options.append(
                option_pattern.substitute(value=quote(str(option_value)))
            )
        space_separated_options = ' '.join(options)
        options_mapping = {}
        options_mapping['options'] = space_separated_options

        if 'executable' in self.config:
            options_mapping['executable'] = self.config['executable']

        for each_option in self.command_options:
            option_value = self.config[each_option]
            if option_value is None:
                # Command options which config option is None
                # should not be passed to command.
                # Its placeholder should be replaced to empty string
                options_mapping[each_option] = ''
                continue

            option_pattern = Template(
                self.command_options[each_option]
            )
            options_mapping[each_option] = \
                option_pattern.substitute(value=quote(str(option_value)))

        command_string = self._command.substitute(
            options_mapping
        )
        return split(command_string)


def create_result_by_returncode(task, returncode, shell_output) -> CheckResult:
    """Create CheckResult based on shell return code.

    .. list-table:: Result status
       :header-rows: 1

       * - Status
         - Description
       * - SUCCESS
         - If checker command exit status is 0
       * - ERROR
         - If checker command exit status is not 0
    """
    if returncode == 0:
        return CheckResult(task.taskname)
    return CheckResult(task.taskname, CheckResult.ERROR, message=shell_output)
