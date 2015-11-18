#!/usr/bin/env python3
# pylint: disable=C0103
"""Example script run by pre-commit hook"""
import sys
from codechecker.checker import PylintChecker
from codechecker.checker import ExitCodeChecker
from codechecker import job_processor
from codechecker import git

ACCEPTED_PYLINT_RATE = 9

# Execute checks only on files added to git staging area
file_list = git.get_staged_files()

py_files = [f for f in file_list if f.endswith('.py')]

# Add checkers
checkers = []
checkers.append(ExitCodeChecker('python3 -m unittest discover .',
                                'python unittest'))
for file_name in py_files:
    checkers.append(PylintChecker(file_name, ACCEPTED_PYLINT_RATE))
    checkers.append(ExitCodeChecker('pep8 {}'.format(file_name),
                                    'PEP8: {}'.format(file_name)))

sys.exit(job_processor.process_jobs(checkers))
