#!/usr/bin/env python3
import multiprocessing as mp
from subprocess import Popen, PIPE

from checker import CheckResult
from checker import PylintCheck
from checker import check_unittest
import printer


WORKERS_COUNT = mp.cpu_count()


def get_staged_files():
    git_args = 'git diff --staged --name-only'.split()
    git_process = Popen(git_args, stdout=PIPE)
    git_process.wait()

    # Filter deleted files
    file_list = [f for f in [f.strip().decode(sys.stdout.encoding)
                             for f in git_process.stdout.readlines()]\
                    if os.path.exists(f) or True]
    return file_list

if __name__ == '__main__':
    import os
    import sys

    # Prepare files
    file_list = get_staged_files()
    py_files = [f for f in file_list if f.endswith('.py')]
    # Exclude test cases
    py_files = [f for f in py_files if not os.path.basename(f).startswith('test_')]

    # Add jobs
    jobs = []
    jobs.append(check_unittest)
    for file_name in py_files:
        jobs.append(PylintCheck(file_name))

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
        sys.exit(0)
    else:
        sys.exit(1)
