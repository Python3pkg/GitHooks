"""Load checkers from yaml file"""
import sys

import yaml
import fnmatch

from codechecker import job_processor
from codechecker import git
from codechecker.checker.base import ExitCodeChecker
from codechecker.checker.builder import (PylintCheckerFactory,
                                         ExitCodeFileCheckerFactory,
                                         CheckerFactory)


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
    if job_processor.process_jobs(result_checkers):
        sys.exit(1)
    else:
        return 0


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

    def create_file_checker(self, checker_data, file_path):
        if isinstance(checker_data, dict):
            checker_type = next(iter(checker_data))
            config = checker_data[checker_type]
        else:
            checker_type = checker_data
            config = None
        factory = self._get_checker_factory(checker_type)
        return factory.create_for_file(file_path, config)

    def create_file_checkers(self, file_path, checkers_list):
        """Create specified checkers for given file"""
        return [self.create_file_checker(checker_data, file_path)
                for checker_data in checkers_list]

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
