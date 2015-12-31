"""Define checkers used in yml file.

This module map checkers used in precommit-checkers.yml to classes creating
checkers tasks.
"""
import re

from codechecker.checker.task import CheckResult


_RE_CODE_RATE = re.compile(r'Your code has been rated at (-?[\d\.]+)/10')
_RE_PYLINT_MESSAGE = re.compile(
    r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)


def create_pylint_result(task, _, shell_output):
    """Create check result for pylint checker."""
    accepted_code_rate = task.config['accepted-code-rate']
    actual_code_rate = float(_RE_CODE_RATE.findall(shell_output)[0])
    if actual_code_rate == 10:
        return CheckResult(task.taskname)

    if actual_code_rate >= accepted_code_rate:
        status = CheckResult.WARNING
        summary = 'Code Rate {0:.2f}/10'.format(actual_code_rate)
    else:
        status = CheckResult.ERROR
        summary = 'Failed: Code Rate {0:.2f}/10'.format(actual_code_rate)
    messages = '\n'.join(_RE_PYLINT_MESSAGE.findall(shell_output))
    return CheckResult(task.taskname, status, summary, messages)


PROJECT_CHECKERS = {
    'unittest': {
        'taskname': 'python unittest',
        'command': 'python -m unittest discover .'
    }
}


FILE_CHECKERS = {
    'pep8': {
        'taskname': 'PEP8 ${file_relpath}',
        'command': 'pep8 ${file_abspath}'
    },
    'pep257': {
        'taskname': 'PEP257 ${file_relpath}',
        'command': 'pep257 ${file_abspath}'
    },
    'jshint': {
        'taskname': 'JSHint ${file_relpath}',
        'command': 'jshint ${options} ${file_abspath}',
        'defaultconfig': {
            'config': '.jshintrc'
        },
        'command_options': {'config': '--config ${value}'}
    },
    'pylint': {
        'taskname': 'Pylint ${file_relpath}',
        'command': 'pylint -f parseable ${file_abspath} ${options}',
        'defaultconfig': {
            'rcfile': None,
            'accepted-code-rate': 9
        },
        'command_options': {'rcfile': '--rcfile=${value}'},
        'result_creator': create_pylint_result
    }
}
