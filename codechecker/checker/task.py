"""Base checker classes.

Exports:

* :class:`CheckResult`: Result of checker execution.
* :class:`Task`: Run checker and return result.
* :class:`Config`: Handle task configuration.
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
        self._command = command
        if config is None:
            self.config = Config({})
        elif isinstance(config, Config):
            self.config = config
        else:
            self.config = Config(config)
        self.result_creator = create_result_by_returncode

    def __call__(self):
        """Execute checker and return check result.

        :rtype: codechecker.checker.task.CheckResult
        """
        returncode, stdout = self._execute_shell_command()
        return self.result_creator(self, returncode, stdout)

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


class Config:
    # pylint: disable=too-few-public-methods
    """Handle configuration.

    Config object is initialized by :class:`dict` but every option is accessed
    through object attribute.

    >>> from codechecker.checker.task import Config
    >>> config = Config({'option':'value'})
    >>> config.option
    'value'

    Config object can contain options created during initialization only.
    After initialization, trying to set new option raises
    :exc:`InvalidConfigOptionError` but value of existing option can always be
    changed.
    """

    def __init__(self, options):
        """Set default configuration."""
        if not isinstance(options, dict):
            raise ValueError(
                '{} (type: {}) is not valid config options. dict required.'
                .format(options, type(options))
            )
        super(Config, self).__setattr__('_options', options)

    def __getattribute__(self, option):
        """Get config option."""
        try:
            return object.__getattribute__(self, '_options')[option]
        except KeyError:
            raise InvalidConfigOptionError(
                '"{}" is not valid config option.'.format(option)
            )

    def __setattr__(self, option, value):
        """Set config option."""
        if option not in self:
            raise InvalidConfigOptionError(
                '"{}" is not valid config option.'.format(option)
            )
        options = object.__getattribute__(self, '_options')
        options[option] = value

    def __contains__(self, option):
        """Check if option exists.

        :rtype: bool
        """
        options = object.__getattribute__(self, '_options')
        return option in options


def create_result_by_returncode(task, returncode, shell_output) -> CheckResult:
    """Create CheckResult based on shell return code."""
    if returncode == 0:
        return CheckResult(task.taskname)
    return CheckResult(task.taskname, CheckResult.ERROR, message=shell_output)


class InvalidConfigOptionError(ValueError):
    """Thrown if invalid option is passed to checker factory config."""

    pass
