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

from codechecker.checker.base import (PylintChecker,
                                      ExitCodeChecker)
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
        checker = creator()
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
        return factory.create_for_file(file_path, config)

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


class _CheckerFactory:
    """Base checker factory."""

    default_config = {}
    checker_name = 'abstract checker'

    def __init__(self):
        """Initialize factory with default config."""
        self.config = copy.copy(self.default_config)

    def set_config(self, config):
        """Overwrite default configuration.

        :type config: dict
        :raises: :exc:`ValueError` if passed config contains invalid option
        """
        self.config = self._mixin_config(config)

    def _mixin_config(self, config):
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
                    .format(option_name, self.checker_name)
                raise ValueError(msg)
            result_config[option_name] = option_value
        return result_config


class PylintCheckerFactory(_CheckerFactory):
    """Create :class:`codechecker.checker.base.PylintChecker`."""

    default_config = {
        'accepted_code_rate': 9,
        'rcfile': None
    }
    checker_name = 'pylint'

    def create_for_file(self, file_path, config=None):
        """Create pylint checker for passed file."""
        config = self._mixin_config(config)
        accepted_code_rate = config['accepted_code_rate']
        abspath = git.abspath(file_path)
        checker = PylintChecker(file_path, abspath, accepted_code_rate)
        if config['rcfile']:
            checker.rcfile = config['rcfile']
        return checker


class ExitCodeFileCheckerFactory(_CheckerFactory):
    """Create :class:`codechecker.checker.base.ExitCodeChecker`."""

    default_config = {'command-options': ''}
    checker_name = 'exit code checker'

    def __init__(self, command_pattern, taskname_pattern):
        """Set command and task name pattern."""
        super(ExitCodeFileCheckerFactory, self).__init__()
        self.command_pattern = Template(command_pattern)
        self.taskname_pattern = Template(taskname_pattern)

    def create_for_file(self, file_path, config=None):
        """Create ExitCodeChecker for passed file."""
        config = self._mixin_config(config)
        command_pattern_params = {'file_path': git.abspath(file_path)}
        if self._is_additional_options_expected():
            command_options = config['command-options']
            command_pattern_params['options'] = command_options
        command = self.command_pattern.substitute(command_pattern_params)
        task_name = self.taskname_pattern.substitute(file_path=file_path)

        return ExitCodeChecker(command, task_name)

    def _is_additional_options_expected(self):
        return self.command_pattern.template.find('$options ') >= 0 \
            or self.command_pattern.template.find('${options}') >= 0 \
            or self.command_pattern.template.endswith('$options')


class InvalidCheckerError(ValueError):
    """Exception thrown if trying to access checker with invalid name."""

    pass


class InvalidConfigOption(ValueError):
    """Thrown if invalid option is passed to checker factory config."""

    pass
