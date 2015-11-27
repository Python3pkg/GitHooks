"""Load checkers from yaml file"""
import yaml
import copy
import fnmatch
from string import Template

from codechecker import job_processor
from codechecker import git
from codechecker.checker import ExitCodeChecker
from codechecker.checker import PylintChecker


def main():
    checker_factory = CheckerFactoryDelegator()
    checker_factory.register_all_factories()
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))

    project_checkers = checkers_data['project-checkers'] \
        if 'project-checkers' in checkers_data else []
    file_checkers = checkers_data['file-checkers'] \
        if 'file-checkers' in checkers_data else {}
    checkers_config = checkers_data['config'] \
        if 'config' in checkers_data else {}

    for each_checkername, each_checkerconf in checkers_config.items():
        checker_factory.set_checker_config(each_checkername, each_checkerconf)

    result_checkers = []

    # Create project checkers
    for each_checkername in project_checkers:
        checker = checker_factory.create_checker(each_checkername)
        if isinstance(checker, list):
            result_checkers.extend(checker)
        else:
            result_checkers.append(checker)

    # Create checkers for staged files
    staged_files = git.get_staged_files()
    files_already_matched = set()
    patterns_sorted = sort_file_patterns(file_checkers.keys())
    for path_pattern in patterns_sorted:
        checkers_list = file_checkers[path_pattern]
        matched_files = set(fnmatch.filter(staged_files, path_pattern))
        matched_files -= files_already_matched
        files_already_matched.update(matched_files)
        for each_file in matched_files:
            result_checkers.extend(checker_factory.create_file_checkers(
                each_file, checkers_list
            ))

    # Execute checkers
    job_processor.process_jobs(result_checkers)


def sort_file_patterns(pattern_list):
    """Sort file patterns

    Sort file patterns so that more specific patterns are befor more generic
    patterns. For example if we have patterns ['*.py', 'tests/*.py'] result
    should be ['tests/*.py', '*.py']"""
    patterns_sorted = []
    for pattern_to_insert in pattern_list:
        for index, pattern_inserted in enumerate(patterns_sorted):
            if fnmatch.fnmatch(pattern_to_insert, pattern_inserted):
                # more generic pattern is already inserted into result list
                # so pattern_to_insert must by inserted before
                patterns_sorted.insert(index, pattern_to_insert)
                break
        else:
            # there is no more generic patterns in result list
            patterns_sorted.append(pattern_to_insert)
    return patterns_sorted


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
        for option_name, option_value in config.items():
            if option_name not in self.default_config:
                msg = '{} is not valid option for {}' \
                    .format(option_name, self.checker_name)
                raise ValueError(msg)
            self.config[option_name] = option_value

    def get_config_option(self, option_name):
        """Get config option from factory configuration"""
        try:
            return self.config[option_name]
        except KeyError:
            msg = '{} is not valid option for {}' \
                    .format(self.checker_name, option_name)
            raise KeyError(msg)


class PylintCheckerFactory(CheckerFactory):
    """Handle PylintChecker creation"""

    default_config = {
        'accepted_code_rate': 9
    }

    def __init__(self):
        """Copy default configuration to instance"""
        self.config = copy.copy(self.default_config)

    def create_for_file(self, file_path):
        """Create pylint checker for passed file"""
        accepted_code_rate = self.get_config_option('accepted_code_rate')
        checker = PylintChecker(file_path, accepted_code_rate)
        checker.set_abspath(git.abspath(file_path))
        return checker


class ExitCodeFileCheckerFactory(CheckerFactory):
    default_config = {'command-options': ''}

    def __init__(self, command_pattern, taskname_pattern):
        """Set command and task name pattern"""
        super(ExitCodeFileCheckerFactory, self).__init__()
        self.command_pattern = Template(command_pattern)
        self.taskname_pattern = Template(taskname_pattern)

    def create_for_file(self, file_path):
        """Create ExitCodeChecker for passed file"""
        command_pattern_params = {'file_path': git.abspath(file_path)}
        command_options = self.get_config_option('command-options')
        if self.is_additional_options_expected():
            command_pattern_params['options'] = command_options
        command = self.command_pattern.substitute(command_pattern_params)
        task_name = self.taskname_pattern.substitute(file_path=file_path)

        return ExitCodeChecker(command, task_name)

    def is_additional_options_expected(self):
        return self.command_pattern.template.find('$options ') >= 0 \
            or self.command_pattern.template.find('${options}') >= 0


class CheckerFactoryDelegator:
    """Delegate requests to proper checker factory

    Delegate requests (checker creation, setting config to checker factory)
    to proper factory
    """

    def __init__(self):
        self.factories = {}

    def create_checker(self, checker_name):
        """Create checker by passed checker name"""
        factory = self._get_checker_factory(checker_name)
        if callable(factory):
            return factory()
        else:
            return factory.create()

    def create_file_checker(self, checker_name, file_path):
        factory = self._get_checker_factory(checker_name)
        return factory.create_for_file(file_path)

    def create_file_checkers(self, file_path, checker_names):
        """Create specified checkers for given file"""
        return [self.create_file_checker(checker_name, file_path)
                for checker_name in checker_names]

    def set_checker_config(self, checker_name, config):
        """Set config to factory corresponding to passed checker name"""
        factory = self._get_checker_factory(checker_name)
        factory.set_config(config)

    def register_factory(self, checker_name, factory):
        """Add checker factory to delegator"""
        if isinstance(factory, CheckerFactory):
            factory.checker_name = checker_name
        self.factories[checker_name] = factory

    def register_all_factories(self):
        self.register_factory(
            'unittest',
            lambda: ExitCodeChecker('python3 -m unittest discover .',
                                    'python unittest')
        )
        self.register_factory(
            'pep8',
            ExitCodeFileCheckerFactory('pep8 $file_path', 'PEP8 $file_path')
        )
        self.register_factory('pylint', PylintCheckerFactory())
        self.register_factory(
            'jshint',
            ExitCodeFileCheckerFactory('jshint $options $file_path',
                                       'JSHint $file_path')
        )

    def _get_checker_factory(self, checker_name):
        """Get checker factory by passed checker name"""
        try:
            factory = self.factories[checker_name]
        except KeyError:
            raise RuntimeError('Invalid checker name {}'.format(checker_name))
        return factory
