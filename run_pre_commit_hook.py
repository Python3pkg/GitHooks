#!/usr/bin/env python3
"""Example script run by pre-commit hook"""
import os
import sys

#uncomment below line after you move this script to main repository
#sys.path.append(os.path.abspath('./GitHooks/'))
from checker import PylintChecker
from checker import PEP8Checker
from checker import check_unittest
import job_processor
import helper

# Prepare files
file_list = helper.get_staged_files()
py_files = [f for f in file_list if f.endswith('.py')]
# Exclude test cases
py_files = [f for f in py_files if not os.path.basename(f).startswith('test_')]

# Add jobs
jobs = []
jobs.append(check_unittest)
for file_name in py_files:
    jobs.append(PylintChecker(file_name))
    jobs.append(PEP8Checker(file_name))

sys.exit(job_processor.process_jobs(jobs))
