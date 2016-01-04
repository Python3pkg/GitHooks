"""Create checkers.

Classes:

- :class:`CheckListBuilder`: Build checkers list
- :class:`PylintCheckerFactory`: Create pylint checker for specified file
- :class:`ExitCodeFileCheckerFactory`: Create exit code checker for
   specified file

Exceptions:

- :exc:`InvalidCheckerError`
- :exc:`InvalidConfigOption`
"""

import copy
from string import Template

from codechecker.checker.task import Task
from codechecker import git


class CheckListBuilder:
    """Build list of checkers.

    Public methods:

    - :meth:`add_project_checker`
    - :meth:`add_checkers_for_file`: Add all checkers for specified file
    - :meth:`configure_checker`: Change checker global configuration
    - :meth:`get_result`: Get prepared list of checkers
    """

    def __init__(self, projectchecker_factories, filecheckers_factories):
        """Set checker factories.

        :param projectchecker_factories: dict mapping checker name to project
            checker factory
        :type projectchecker_factories: dict
        :param filecheckers_factories: dict mapping checker name to file
            checker factory
        :type filecheckers_factories: dict
        """
        self._checker_tasks = []
        self._projectchecker_factories = projectchecker_factories
        self._filecheckers_factories = filecheckers_factories

    def add_project_checker(self, name):
        """Add project checker.

        :param name: project checker name
        :type name: string
        :raises: :exc:`InvalidCheckerError` If there is not checker with
            specified name
        """
        try:
            creator = self._projectchecker_factories[name]
        except KeyError:
            raise InvalidCheckerError(
                '"{}" is invalid project checker'.format(name)
            )
        checker = creator.create()
        self._checker_tasks.append(checker)

    def add_checkers_for_file(self, file_path, checkers_list):
        """Create specified checkers for given file.

        :raises: :exc:`InvalidCheckerError` If factory for specified checker
            name not found
        """
        checkers = [self._create_file_checker(checker_data, file_path)
                    for checker_data in checkers_list]
        self._checker_tasks.extend(checkers)

    def configure_checker(self, name, config):
        """Change global checker.

        :raises: :exc:`InvalidCheckerError` If factory for specified checker
            name not found
        """
        if name in self._projectchecker_factories:
            checker = self._projectchecker_factories[name]
        elif name in self._filecheckers_factories:
            checker = self._filecheckers_factories[name]
        else:
            raise InvalidCheckerError('Can not set config to checker. '
                                      'Checker "{}" is invalid'.format(name))
        checker.set_config(config)

    def get_result(self):
        """Return built checkers list."""
        return self._checker_tasks

    def _create_file_checker(self, checker_data, file_path):
        """Create file checker.

        checker_data should be checker name or dict. If checker_data is dict
        then its key is checker name and value is checker config.

        :raises: :exc:`InvalidCheckerError` If factory for specified checker
            name not found
        """
        if isinstance(checker_data, dict):
            checkername = next(iter(checker_data))
            config = checker_data[checkername]
        else:
            checkername = checker_data
            config = None
        factory = self._get_filechecker_factory(checkername)
        return factory.create(file_path, config)

    def _get_filechecker_factory(self, checkername):
        """Get factory for file checker.

        :raises: :exc:`InvalidCheckerError` If factory for specified checker
            name not found
        """
        try:
            return self._filecheckers_factories[checkername]
        except KeyError:
            raise InvalidCheckerError(
                '"{}" is invalid file checker'.format(checkername)
            )


class TaskCreator:
    """Create :class:`codechecker.checker.task.Task` objects."""

    def __init__(self, checkername, taskname, command, defaultconfig=None,
                 command_options=None, result_creator=None):
        """Set checker data."""
        # pylint: disable=too-many-arguments
        self._checkername = checkername
        self._taskname = Template(taskname)
        self._command = Template(command)
        self.config = defaultconfig if defaultconfig else {}
        self._command_options = command_options
        self._result_creator = result_creator

    def create(self, relpath=None, config=None):
        """Create Task for specified file."""
        config = self._mix_config(config)
        if relpath:
            abspath = git.abspath(relpath)
            command = self._command.safe_substitute(file_abspath=abspath)
            taskname = self._taskname.substitute(file_relpath=relpath)
        else:
            taskname = self._taskname.template
            command = self._command.template

        task = Task(taskname, command, config)
        if self._command_options:
            task.command_options = self._command_options
        if self._result_creator:
            task.result_creator = self._result_creator
        return task

    def set_config(self, config):
        """Overwrite default configuration.

        :type config: dict
        :raises: :exc:`ValueError` if passed config contains invalid option
        """
        self.config = self._mix_config(config)

    def _mix_config(self, config):
        """Get joined factory config with passed one.

        This method does not change factory configuration, it returns new
        configuration object instead.
        """
        if not config:
            return copy.copy(self.config)
        result_config = copy.copy(self.config)
        for option_name, option_value in config.items():
            if option_name not in self.config:
                msg = '"{}" is not valid option for "{}"' \
                    .format(option_name, self._checkername)
                raise ValueError(msg)
            result_config[option_name] = option_value
        return result_config


class InvalidCheckerError(ValueError):
    """Exception thrown if trying to access checker with invalid name."""

    pass


class InvalidConfigOption(ValueError):
    """Thrown if invalid option is passed to checker factory config."""

    pass
