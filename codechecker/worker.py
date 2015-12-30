"""Execute checkers tasks.

Exports:

- :py:func:`execute_checkers` - Execute checkers
"""
import multiprocessing as mp

from codechecker.checker.task import CheckResult


WORKERS_COUNT = mp.cpu_count()


def execute_checkers(jobs):
    """Execute checkers and return status information.

    Execute checkers passed as argument in couple of concurrent processes,
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
        _print_result(result)
        if result.status == CheckResult.ERROR:
            is_ok = False
    print('-' * 80)
    if is_ok:
        print(_success('OK'))
    else:
        print(_error('Commit aborted'))

    if is_ok:
        return 0
    else:
        return 1


def _print_result(result):
    """Print colorized check result.

    :type value: checker.CheckResult
    """
    if result.summary:
        summary_raw = result.summary
    else:
        summary_raw = _DEFAULT_SUMMARY_TEXT[result.status]
    summary = _SUMMARY_FORMAT[result.status](summary_raw)
    taskname = _bold(result.taskname)

    print('* {task}: {summary}'.format(task=taskname, summary=summary))
    if result.message:
        print(result.message)


def _error(text):
    """Colorize terminal output to bold red."""
    return '\033[1m\033[31m{text}\033[0m'.format(text=text)


def _success(text):
    """Colorize terminal output to bold green."""
    return '\033[1m\033[32m{text}\033[0m'.format(text=text)


def _warning(text):
    """Colorize terminal output to bold yellow."""
    return '\033[1m\033[33m{text}\033[0m'.format(text=text)


def _info(text):
    """Colorize terminal output to bold blue."""
    return '\033[1m\033[34m{text}\033[0m'.format(text=text)


def _bold(text):
    """Colorize terminal output to bold."""
    return '\033[1m{text}\033[0m'.format(text=text)


_DEFAULT_SUMMARY_TEXT = {
    CheckResult.SUCCESS: 'OK',
    CheckResult.WARNING: 'OK',
    CheckResult.ERROR: 'FAILED'
}

_SUMMARY_FORMAT = {
    CheckResult.SUCCESS: _success,
    CheckResult.WARNING: _warning,
    CheckResult.ERROR: _error
}
