"""Execute checkers defined in precommit-checkers.yml.

see :func:`codechecker.scripts.runner.main`
"""
import sys
import fnmatch

import yaml

from codechecker import job_processor
from codechecker import git
from codechecker.checker.builder import CheckListBuilder
from codechecker.concrete_checkers import (get_projectcheckers,
                                           get_filecheckers)


def main():
    """Run checkers.

    1. Load checkers configuration from precommit-checkers.yml

    2. Use :py:class:`codechecker.checker.builder.CheckListBuilder` to create
    list of all configured checkers for project and staged files

    3. Next call :py:func:`codechecker.job_processor.execute_checkers` to
    execute created checker tasks and print checkers result

    4. If :py:func:`codechecker.job_processor.execute_checkers` return non
    empty value script exits with status 1 so commit is aborted
    """
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))
    _validate_checkers_data(checkers_data)
    checklist_builder = _init_checkers_builder()
    if 'config' in checkers_data:
        _set_checkers_config(checklist_builder, checkers_data['config'])
    if 'project-checkers' in checkers_data:
        _create_project_checkers(checklist_builder,
                                 checkers_data['project-checkers'])
    if 'file-checkers' in checkers_data:
        _create_file_checkers(checklist_builder,
                              checkers_data['file-checkers'])

    return _execute_checkers(checklist_builder.get_result())


def _init_checkers_builder():
    checklist_builder = CheckListBuilder(
        get_projectcheckers(),
        get_filecheckers()
    )
    return checklist_builder


def _validate_checkers_data(checkers_data):
    """Check if precommit-checkers.yml contains valid options only."""
    for each_option in checkers_data:
        if each_option not in ('config', 'project-checkers', 'file-checkers'):
            raise ValueError('precommit-checkers.yml contains'
                             ' invalid option "{}"'.format(each_option))


def _set_checkers_config(checklist_builder, config):
    """Configure checker factories."""
    for each_checker, each_conf in config.items():
        checklist_builder.configure_checker(each_checker, each_conf)


def _create_project_checkers(checklist_builder, checkers):
    """Create project checkers."""
    for each_checker in checkers:
        checklist_builder.add_project_checker(each_checker)


def _create_file_checkers(checklist_builder, checkers):
    """Create file checkers."""
    staged_files = git.get_staged_files()
    files_previously_matched = set()
    patterns_sorted = _sort_file_patterns(checkers.keys())
    for path_pattern in patterns_sorted:
        checkers_list = checkers[path_pattern]
        matched_files = set(fnmatch.filter(staged_files, path_pattern))
        # Exclude files that match more specific pattern
        files_to_check = matched_files - files_previously_matched
        files_previously_matched.update(files_to_check)
        for each_file in files_to_check:
            checklist_builder.add_checkers_for_file(each_file, checkers_list)


def _execute_checkers(checker_tasks):
    if job_processor.execute_checkers(checker_tasks):
        sys.exit(1)
    else:
        return 0


def _sort_file_patterns(pattern_list):
    """Sort file patterns.

    Sort file patterns so that more specific patterns are before more generic
    patterns. For example if we have patterns ['*.py', 'tests/*.py'] result
    should be ['tests/*.py', '*.py']
    """
    patterns_sorted = []
    for pattern_to_insert in pattern_list:
        for index, pattern_inserted in enumerate(patterns_sorted):
            if fnmatch.fnmatch(pattern_to_insert, pattern_inserted):
                # more generic pattern is already inserted into result list
                # so pattern_to_insert must by inserted before
                patterns_sorted.insert(index, pattern_to_insert)
                break
        else:
            # there is not more generic patterns in result list
            patterns_sorted.append(pattern_to_insert)
    return patterns_sorted