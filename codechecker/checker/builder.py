"""Classes making checker tasks"""

import copy
from string import Template

from codechecker.checker.base import (PylintChecker,
                                      ExitCodeChecker)
from codechecker import git


class CheckListBuilder:
    """Build list of checkers"""

    def __init__(self):
        self._checker_tasks = []
        self._projectchecker_creators = {}
        self._filecheckers_creators = {}

    def add_project_checker(self, name):
        creator = self._projectchecker_creators[name]
        checker = creator()
        self._checker_tasks.append(checker)

    def add_all_filecheckers(self, file_path, checkers_list):
        """Create specified checkers for given file"""
        checkers = [self.create_file_checker(checker_data, file_path)
                    for checker_data in checkers_list]
        self._checker_tasks.extend(checkers)

    def create_file_checker(self, checker_data, file_path):
        if isinstance(checker_data, dict):
            checker_type = next(iter(checker_data))
            config = checker_data[checker_type]
        else:
            checker_type = checker_data
            config = None
        factory = self.get_file_checker(checker_type)
        return factory.create_for_file(file_path, config)

    def get_checker_tasks(self):
        return self._checker_tasks

    def get_file_checker(self, checkername):
        return self._filecheckers_creators[checkername]

    def set_checker_config(self, name, config):
        if name in self._projectchecker_creators:
            checker = self._projectchecker_creators[name]
        elif name in self._filecheckers_creators:
            checker = self._filecheckers_creators[name]
        else:
            raise KeyError('Can not set config to checker. '
                           'Checker "{}" not found'.format(name))
        checker.set_config(config)

    def register_projectchecker(self, name_to_creator_map):
        for name, creator in name_to_creator_map.items():
            self._projectchecker_creators[name] = creator

    def register_filechecker(self, name_to_creator_map):
        for name, creator in name_to_creator_map.items():
            self._filecheckers_creators[name] = creator


class CheckerFactory:
    default_config = {}
    checker_name = 'abstract checker'

    def __init__(self):
        """Copy default configuration to instance"""
        self.config = copy.copy(self.default_config)

    def set_config(self, config):
        """Overwrite default configuration

        :type config: dict
        :raises: :exc:`ValueError` if passed config contains invalid option
        """
        self.config = self._mixin_config(config)

    def get_config_option(self, option_name):
        """Get config option from factory configuration"""
        try:
            return self.config[option_name]
        except KeyError:
            msg = '{} is not valid option for {}' \
                    .format(self.checker_name, option_name)
            raise KeyError(msg)

    def _mixin_config(self, config):
        """Join config set in factory with passed one

        Join config set in factory with passed one and return result"""
        if not config:
            return copy.copy(self.config)
        result_config = {}
        for option_name, option_value in config.items():
            if option_name not in self.config:
                msg = '{} is not valid option for {}' \
                    .format(option_name, self.checker_name)
                raise ValueError(msg)
            result_config[option_name] = option_value
        return result_config


class PylintCheckerFactory(CheckerFactory):
    """Create :py:class:`PylintChecker`"""

    default_config = {
        'accepted_code_rate': 9
    }

    def create_for_file(self, file_path, config=None):
        """Create pylint checker for passed file"""
        config = self._mixin_config(config)
        accepted_code_rate = config['accepted_code_rate']
        checker = PylintChecker(file_path, accepted_code_rate)
        checker.set_abspath(git.abspath(file_path))
        return checker


class ExitCodeFileCheckerFactory(CheckerFactory):
    """Create :py:class:`ExitCodeChecker`"""
    default_config = {'command-options': ''}

    def __init__(self, command_pattern, taskname_pattern):
        """Set command and task name pattern"""
        super(ExitCodeFileCheckerFactory, self).__init__()
        self.command_pattern = Template(command_pattern)
        self.taskname_pattern = Template(taskname_pattern)

    def create_for_file(self, file_path, config=None):
        """Create ExitCodeChecker for passed file"""
        config = self._mixin_config(config)
        command_pattern_params = {'file_path': git.abspath(file_path)}
        command_options = config['command-options']
        if self.is_additional_options_expected():
            command_pattern_params['options'] = command_options
        command = self.command_pattern.substitute(command_pattern_params)
        task_name = self.taskname_pattern.substitute(file_path=file_path)

        return ExitCodeChecker(command, task_name)

    def is_additional_options_expected(self):
        return self.command_pattern.template.find('$options ') >= 0 \
            or self.command_pattern.template.find('${options}') >= 0
