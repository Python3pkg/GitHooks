"""Module responsible for executing checker tasks

Exports:
    :py:func:`process_jobs` - Execute jobs
"""
import multiprocessing as mp

from codechecker.checker.base import CheckResult
from codechecker import printer


WORKERS_COUNT = mp.cpu_count()


def process_jobs(jobs):
    """Execute jobs and return success information

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
