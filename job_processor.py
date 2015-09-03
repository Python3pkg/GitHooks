#!/usr/bin/env python3
import os
import sys
import multiprocessing as mp
from subprocess import Popen, PIPE

from checker import CheckResult
import printer


WORKERS_COUNT = mp.cpu_count()


def get_staged_files():
    """Return files in git staging area"""
    git_args = 'git diff --staged --name-only'.split()
    git_process = Popen(git_args, stdout=PIPE)
    git_process.wait()

    # Filter deleted files
    file_list = [f for f in [f.strip().decode(sys.stdout.encoding)
                             for f in git_process.stdout.readlines()]\
                    if os.path.exists(f) or True]
    return file_list

def process_jobs(jobs):
    """Execute checkers and return success information

    Execute jobs passed as argument in couple of concurrent processes,
    for every job prints result information
    and return value indicating if all jobs succeed.

    :return: 0 if all checks passed, 1 if at least one does not
    :rtype: integer
    """
    # Prepare workers and process jobs
    pool = mp.Pool(processes=WORKERS_COUNT)
    results = [pool.apply_async(job) for job in jobs]

    # Check results
    is_ok = True
    for result in results:
        result = result.get()
        printer.print_result(result)
        if result.status == CheckResult.ERROR:
            is_ok = False
    print('-' * 80)
    if is_ok:
        print(printer.success('OK'))
    else:
        print(printer.error('Commit aborted'))

    if is_ok:
        return 0
    else:
        return 1
