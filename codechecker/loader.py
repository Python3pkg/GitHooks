"""Module responsible for loading checkers

see :py:func:`codechecker.loader.main`"""
import sys
import fnmatch

import yaml

from codechecker import job_processor
from codechecker import git
from codechecker.checker.base import ExitCodeChecker
from codechecker.checker.builder import (CheckListBuilder,
                                         PylintCheckerFactory,
                                         ExitCodeFileCheckerFactory)


def main():
    """Load checkers

    1. Load checkers configuration from precommit-checkers.yml
    2. Use :py:class:`codechecker.checker.builder.CheckListBuilder` to create
        list of all configured checkers for project and staged files
    3. Next call :py:func:`codechecker.job_processor.process_jobs` to execute
        created checker tasks and print checkers result
    4. If :py:func:`codechecker.job_processor.process_jobs` return non empty
        value script exits with status 1 so commit is aborted"""
    checklist_builder = CheckListBuilder()
    checklist_builder.register_projectcheckers(
        _get_projectcheckers_creators()
    )
    checklist_builder.register_filecheckers(
        _get_filechecker_creators()
    )
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))

    # Check if precommit-checkers.yml contains valid options only
    for each_option in checkers_data:
        if each_option not in ('config', 'project-checkers', 'file-checkers'):
            raise ValueError('precommit-checkers.yml contains'
                             ' invalid option "{}"'.format(each_option))

    if 'config' in checkers_data:
        _set_checkers_config(checklist_builder, checkers_data['config'])
    if 'project-checkers' in checkers_data:
        _create_project_checkers(checklist_builder,
                                 checkers_data['project-checkers'])
    if 'file-checkers' in checkers_data:
        _create_file_checkers(checklist_builder,
                              checkers_data['file-checkers'])

    # Execute checkers
    checker_tasks = checklist_builder.get_checker_tasks()
    if job_processor.process_jobs(checker_tasks):
        sys.exit(1)
    else:
        return 0


def _set_checkers_config(checklist_builder, config):
    """Configure checker factories"""
    for each_checker, each_conf in config.items():
        checklist_builder.set_checker_config(each_checker,
                                             each_conf)


def _create_project_checkers(checklist_builder, checkers):
    """Create project checkers"""
    for each_checker in checkers:
        checklist_builder.add_project_checker(each_checker)


def _create_file_checkers(checklist_builder, checkers):
    """Create file checkers"""
    staged_files = git.get_staged_files()
    files_already_matched = set()
    patterns_sorted = _sort_file_patterns(checkers.keys())
    for path_pattern in patterns_sorted:
        checkers_list = checkers[path_pattern]
        matched_files = set(fnmatch.filter(staged_files, path_pattern))
        # Exclude files that match more specific pattern
        matched_files -= files_already_matched
        files_already_matched.update(matched_files)
        for each_file in matched_files:
            checklist_builder.add_all_filecheckers(each_file, checkers_list)


def _sort_file_patterns(pattern_list):
    """Sort file patterns

    Sort file patterns so that more specific patterns are before more generic
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


def _get_projectcheckers_creators():
    return {
        'unittest': lambda: ExitCodeChecker('python -m unittest discover .',
                                            'python unittest')
    }


def _get_filechecker_creators():
    return {
        'pep8': ExitCodeFileCheckerFactory('pep8 $file_path',
                                           'PEP8 $file_path'),
        'pylint': PylintCheckerFactory(),
        'jshint': ExitCodeFileCheckerFactory('jshint $options $file_path',
                                             'JSHint $file_path')
    }
