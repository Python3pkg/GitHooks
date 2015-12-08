"""Load checkers from yaml file"""
import sys

import yaml
import fnmatch

from codechecker import job_processor
from codechecker import git
from codechecker.checker.base import ExitCodeChecker
from codechecker.checker.builder import (CheckListBuilder,
                                         PylintCheckerFactory,
                                         ExitCodeFileCheckerFactory)


def main():
    checklist_builder = CheckListBuilder()
    checklist_builder.register_projectchecker(
        _PROJECT_CHECKER_CREATORS
    )
    checklist_builder.register_filechecker(
        _FILE_CHECKER_CREATORS
    )
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))

    project_checkers = checkers_data['project-checkers'] \
        if 'project-checkers' in checkers_data else []
    file_checkers = checkers_data['file-checkers'] \
        if 'file-checkers' in checkers_data else {}
    checkers_config = checkers_data['config'] \
        if 'config' in checkers_data else {}

    for each_checkername, each_checkerconf in checkers_config.items():
        checklist_builder.set_checker_config(each_checkername,
                                             each_checkerconf)

    # Create project checkers
    for each_checkername in project_checkers:
        checklist_builder.add_project_checker(each_checkername)

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
            checklist_builder.add_all_filecheckers(each_file, checkers_list)

    # Execute checkers
    result_checkers = checklist_builder.get_checker_tasks()
    if job_processor.process_jobs(result_checkers):
        sys.exit(1)
    else:
        return 0


def sort_file_patterns(pattern_list):
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


_PROJECT_CHECKER_CREATORS = {
    'unittest': lambda: ExitCodeChecker('python3 -m unittest discover .',
                                        'python unittest')
}


_FILE_CHECKER_CREATORS = {
    'pep8': ExitCodeFileCheckerFactory('pep8 $file_path', 'PEP8 $file_path'),
    'pylint': PylintCheckerFactory(),
    'jshint': ExitCodeFileCheckerFactory('jshint $options $file_path',
                                         'JSHint $file_path')
}
