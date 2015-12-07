"""Module for printing :py:class:`checker.CheckResult` in terminal"""

from codechecker.checker.base import CheckResult


def print_result(result):
    """Print colorized check result

    :type value: checker.CheckResult
    """
    if result.summary:
        summary_raw = result.summary
    else:
        summary_raw = _DEFAULT_SUMMARY_TEXT[result.status]
    summary = _SUMMARY_FORMAT[result.status](summary_raw)
    task_name = bold(result.task_name)

    print('* {task}: {summary}'.format(task=task_name, summary=summary))
    if result.info:
        print(info(result.info))
    if result.message:
        print(result.message)


def error(text):
    """Colorize terminal output to bold red"""
    return '\033[1m\033[31m{text}\033[0m'.format(text=text)


def success(text):
    """Colorize terminal output to bold green"""
    return '\033[1m\033[32m{text}\033[0m'.format(text=text)


def warning(text):
    """Colorize terminal output to bold yellow"""
    return '\033[1m\033[33m{text}\033[0m'.format(text=text)


def info(text):
    """Colorize terminal output to bold blue"""
    return '\033[1m\033[34m{text}\033[0m'.format(text=text)


def bold(text):
    """Colorize terminal output to bold"""
    return '\033[1m{text}\033[0m'.format(text=text)


_DEFAULT_SUMMARY_TEXT = {
    CheckResult.SUCCESS: 'OK',
    CheckResult.WARNING: 'OK',
    CheckResult.ERROR: 'FAILED'
}

_SUMMARY_FORMAT = {
    CheckResult.SUCCESS: success,
    CheckResult.WARNING: warning,
    CheckResult.ERROR: error
}
