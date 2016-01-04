"""Define checkers used in yml file.

This module map checkers used in precommit-checkers.yml to classes creating
checkers tasks.
"""


from codechecker.result_creators import (create_pylint_result,
                                         create_pyunittest_result,
                                         create_phpunit_result)


TASKNAME, COMMAND, DEFAULTCONFIG, COMMAND_OPTIONS, RESULT_CREATOR, \
    COMMAND_OPTIONS_ORDER, REQUIRED_OPTIONS = \
    'taskname', 'command', 'defaultconfig', 'command_options', \
    'result_creator', 'command_options_order', 'required_options'


PROJECT_CHECKERS = {
    'unittest': {
        TASKNAME: 'PYTHON UNITTEST',
        COMMAND: 'python -m unittest discover .',
        RESULT_CREATOR: create_pyunittest_result
    },
    'phpunit': {
        TASKNAME: 'PHPUNIT',
        COMMAND: '${executable} ${bootstrap} ${directory}',
        DEFAULTCONFIG: {
            'executable': 'phpunit',
            'directory': None,
            'bootstrap': None
        },
        COMMAND_OPTIONS: {
            'bootstrap': '--bootstrap ${value}',
            'directory': '${value}'
        },
        RESULT_CREATOR: create_phpunit_result
    }
}


FILE_CHECKERS = {
    'pep8': {
        TASKNAME: 'PEP8 ${file_relpath}',
        COMMAND: 'pep8 ${file_abspath}'
    },
    'pep257': {
        TASKNAME: 'PEP257 ${file_relpath}',
        COMMAND: 'pep257 ${file_abspath}'
    },
    'jshint': {
        TASKNAME: 'JSHint ${file_relpath}',
        COMMAND: 'jshint ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'config': '.jshintrc'
        },
        COMMAND_OPTIONS: {'config': '--config ${value}'}
    },
    'pylint': {
        TASKNAME: 'Pylint ${file_relpath}',
        COMMAND: 'pylint -f parseable ${file_abspath} ${options}',
        DEFAULTCONFIG: {
            'rcfile': None,
            'accepted-code-rate': 9
        },
        COMMAND_OPTIONS: {'rcfile': '--rcfile=${value}'},
        RESULT_CREATOR: create_pylint_result
    }
}
