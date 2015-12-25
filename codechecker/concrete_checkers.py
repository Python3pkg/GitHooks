"""Define checkers used in yml file.

This module map checkers used in precommit-checkers.yml to classes creating
checkers tasks.
"""
from codechecker.checker.builder import (PylintCheckerFactory,
                                         ExitCodeFileCheckerFactory)
from codechecker.checker.base import ExitCodeChecker


def get_projectcheckers():
    """Return project checkers factories."""
    return {
        'unittest': lambda: ExitCodeChecker('python -m unittest discover .',
                                            'python unittest')
    }


def get_filecheckers():
    """Return file checkers factories."""
    return {
        'pep8': ExitCodeFileCheckerFactory('pep8 ${file_path}',
                                           'PEP8 ${file_path}'),
        'pylint': PylintCheckerFactory(),
        'pep257': ExitCodeFileCheckerFactory('pep257 ${file_path} ${options}',
                                             'PEP 257 ${file_path}'),
        'jshint': ExitCodeFileCheckerFactory('jshint ${options} ${file_path}',
                                             'JSHint ${file_path}')
    }
