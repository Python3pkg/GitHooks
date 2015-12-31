"""Define checkers used in yml file.

This module map checkers used in precommit-checkers.yml to classes creating
checkers tasks.
"""


from codechecker.result_creators import create_pylint_result


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
