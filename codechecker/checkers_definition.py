"""Define checkers used in yml file.

This module map checkers used in precommit-checkers.yml to classes creating
checkers tasks.
"""


from codechecker.result_creators import (create_pylint_result,
                                         create_pyunittest_result,
                                         create_phpunit_result)


TASKNAME, COMMAND, DEFAULTCONFIG, COMMAND_OPTIONS, RESULT_CREATOR = \
    'taskname', 'command', 'defaultconfig', 'command_options', 'result_creator'


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
    },
    'intern': {
        TASKNAME: 'INTERN',
        COMMAND: '${executable} ${config}',
        DEFAULTCONFIG: {
            'executable': 'intern-client',
            'config': None
        },
        COMMAND_OPTIONS: {
            'config': 'config=${value}'
        }
    }
}


FILE_CHECKERS = {
    'pep8': {
        TASKNAME: 'PEP8 ${file_relpath}',
        COMMAND: 'pep8 ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'config': None,
            'quiet': None,
            'qq': None,
            'first': None,
            'select': None,
            'ignore': None,
            'show-source': None,
            'show-pep8': None,
            'statistics': None,
            'count': None,
            'max-line-length': None,
            'hang-closing': None,
            'format': None
        },
        COMMAND_OPTIONS: {
            'quiet': '--quiet',
            'qq': '-qq',
            'first': '--first',
            'select': '--select=${value}',
            'ignore': '--ignore=${value}',
            'show-source': '--show-source',
            'show-pep8': '--show-pep8',
            'statistics': '--statistics',
            'count': '--count',
            'max-line-length': '--max-line-length=${value}',
            'hang-closing': '--hang-closing',
            'format': '--format=${value}',
            'config': '--config=${value}'
        }
    },
    'pep257': {
        TASKNAME: 'PEP257 ${file_relpath}',
        COMMAND: 'pep257 ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'count': None,
            'select': None,
            'ignore': None,
            'add-select': None,
            'add-ignore': None,
            'explain': None,
            'source': None
        },
        COMMAND_OPTIONS: {
            'count': '--count=${value}',
            'select': '--select=${value}',
            'ignore': '--ignore=${value}',
            'add-select': '--add-select=${value}',
            'add-ignore': '--add-ignore=${value}',
            'explain': '--explain',
            'source': '--source'
        }
    },
    'jshint': {
        TASKNAME: 'JSHint ${file_relpath}',
        COMMAND: '${executable} ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'config': None,
            'executable': 'jshint'
        },
        COMMAND_OPTIONS: {'config': '--config ${value}'}
    },
    'jscs': {
        TASKNAME: 'JSCS ${file_relpath}',
        COMMAND: '${executable} ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'executable': 'jscs',
            'config': None,
            'preset': None,
            'esnext': None,
            'es3': None
        },
        COMMAND_OPTIONS: {
            'config': '--config ${value}',
            'preset': '--preset ${value}',
            'esnext': '--esnext',
            'es3': '--es3'
        }
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
    },
    'phpcs': {
        TASKNAME: 'PHPCS ${file_relpath}',
        COMMAND: '${executable} ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'executable': 'phpcs',
            'encoding': 'utf-8',
            'standard': None
        },
        COMMAND_OPTIONS: {
            'standard': '--standard=${value}',
            'encoding': '--encoding=${value}'
        }
    },
    'rst-lint': {
        TASKNAME: 'reST-lint ${file_relpath}',
        COMMAND: '${executable} ${options} ${file_abspath}',
        DEFAULTCONFIG: {
            'executable': 'rst-lint',
            'encoding': 'utf-8'
        },
        COMMAND_OPTIONS: {
            'encoding': '--encoding ${value}'
        }
    }
}
