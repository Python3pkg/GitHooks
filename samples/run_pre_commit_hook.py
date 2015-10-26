#!/usr/bin/env python3
# pylint: disable=C0103
"""Example script run by pre-commit hook"""
import os
import sys

# uncomment below line after you move this script to main repository
# sys.path.append(os.path.abspath('./GitHooks/'))
from githooks.checker import PylintChecker
from githooks.checker import ExitCodeChecker
from githooks import job_processor
from githooks import helper

ACCEPTED_PYLINT_RATE = 9

# Execute checks only on files added to git staging area
file_list = helper.get_staged_files()
# Exclude deleted files
file_list = [file_name for file_name in file_list if os.path.exists(file_name)]
py_files = [f for f in file_list if f.endswith('.py')]
# Exclude test cases
py_files = [f for f in py_files if not os.path.basename(f).startswith('test_')]

# Add jobs
jobs = []
jobs.append(ExitCodeChecker('python3 -m unittest discover .',
                            'python unittest'))
for file_name in py_files:
    jobs.append(PylintChecker(file_name, ACCEPTED_PYLINT_RATE))
    jobs.append(ExitCodeChecker('pep8 {}'.format(file_name),
                                'PEP8: {}'.format(file_name)))

sys.exit(job_processor.process_jobs(jobs))
