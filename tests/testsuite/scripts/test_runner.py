"""Checker runner test cases"""
import os
from os import path
from unittest import mock
import yaml

from codechecker.scripts import runner
from codechecker.task.task import Task
from codechecker import git
from codechecker.checkers_spec import (PROJECT_CHECKERS,
                                       FILE_CHECKERS)
from codechecker.checkers_spec import (TASKNAME,
                                       COMMAND,
                                       DEFAULTCONFIG,
                                       COMMAND_OPTIONS,
                                       RESULT_CREATOR)
from codechecker.result_creators import (create_result_by_returncode,
                                         create_pylint_result)
from tests.testsuite.scripts import FakeFSTestCase
from tests.comparison import UnOrderedCollectionMatcher


class RunnerTestCase(FakeFSTestCase):
    # pylint: disable=no-member
    """Test cases for code checker runner

    This class test if code checker runner creates proper checkers with proper
    parameters for stashed files"""

    def setUp(self):
        """Create virtual file structure"""
        self.setUpPyfakefs()
        self.repo_root = '/path/to/repository'
        # patch tasks execution
        worker_patcher = mock.patch(
            'codechecker.scripts.runner.worker',
            autospec=True
        )
        self.addCleanup(worker_patcher.stop)
        self.worker = worker_patcher.start()
        self.worker.execute_checkers.return_value = 0
        # patch checkers specification
        file_checkers_patch = mock.patch.dict(FILE_CHECKERS)
        self.addCleanup(file_checkers_patch.stop)
        file_checkers_patch.start()
        project_checkers_patch = mock.patch.dict(PROJECT_CHECKERS)
        self.addCleanup(project_checkers_patch.stop)
        project_checkers_patch.start()
        PROJECT_CHECKERS.clear()
        FILE_CHECKERS.clear()

    def test_project_checker_is_created_only_once(self):
        """Project checker should always be created once."""
        precommit_yaml_contents = yaml.dump({
            'project-checkers': ['unittest']
        })
        self.patch_git_repository(precommit_yaml_contents)
        patch_project_checker('unittest',
                              taskname='python unittest',
                              command='python -m unittest discover .')

        runner.main()

        expected_command = 'python -m unittest discover .'
        expected_task_name = 'python unittest'
        expected = UnOrderedCollectionMatcher([
            Task(expected_task_name, expected_command,
                 create_result_by_returncode)
        ])
        self.worker.execute_checkers.assert_called_once_with(expected)

    def test_file_checker_is_created_for_files_in_index(self):
        """File checker should be created for files from git index."""
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pep8']}
        })
        staged_files = ['module.py',
                        'module2.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker('pep8',
                           taskname='PEP8 ${file_relpath}',
                           command='pep8 ${file_abspath}')

        runner.main()

        expected_checkers = []
        for file_path in staged_files:
            command = 'pep8 {}'.format(git.abspath(file_path))
            task_name = 'PEP8 {}'.format(file_path)
            expected_checkers.append(
                Task(task_name, command, create_result_by_returncode)
            )
        expected_checkers = UnOrderedCollectionMatcher(expected_checkers)
        self.worker.execute_checkers \
            .assert_called_once_with(expected_checkers)

    def test_checkers_can_be_configured_globally(self):
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.js': ['jshint']},
            'config': {
                'jshint': {'config': '.jshintrc'}
            }
        })
        staged_files = ['module.js']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'jshint',
            taskname='JSHint ${file_relpath}',
            command='jshint ${options} ${file_abspath}',
            defaultconfig={
                'config': '.jshintrc'
            },
            command_options={'config': '--config ${value}'}
        )

        runner.main()

        expected_task = Task(
            taskname='JSHint module.js',
            command='jshint --config .jshintrc {}' \
                .format(git.abspath('module.js')),
            result_creator=create_result_by_returncode,
            config={
                'config': '.jshintrc'
            }
        )
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(
                [expected_task]
            )
        )

    def test_checker_is_created_for_every_staged_file_matching_pattern(self):
        """Only files matching pattern should have created checkers."""
        accepted_code_rate = 9
        pylint_config = {
            'rcfile': None,
            'accepted-code-rate': accepted_code_rate
        }
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pylint']}
        })
        staged_files = ['module.py',
                        'module2.py',
                        'module.js']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pylint',
            taskname='Pylint ${file_relpath}',
            command='pylint -f parseable ${file_abspath} ${options}',
            defaultconfig=pylint_config,
            command_options={'rcfile': '--rcfile=${value}'}
        )

        runner.main()

        py_files = [f for f in staged_files if f.endswith('.py')]
        expected_tasks = []
        for each_file in py_files:
            taskname = 'Pylint {}'.format(each_file)
            abspath = git.abspath(each_file)
            command = 'pylint -f parseable {}'.format(abspath)
            task = Task(taskname, command,
                        create_result_by_returncode, pylint_config)
            expected_tasks.append(task)
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_tasks)
        )

    def test_checker_can_be_defined_with_custom_result_creator(self):
        """Checker can have own result creator.

        Result creator builds CheckResult based on stdout, returncode and
        config.
        """
        accepted_code_rate = 9
        pylint_config = {
            'rcfile': None,
            'accepted-code-rate': accepted_code_rate
        }
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pylint']}
        })
        staged_files = ['module.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pylint',
            taskname='Pylint ${file_relpath}',
            command='pylint -f parseable ${file_abspath} ${options}',
            defaultconfig=pylint_config,
            command_options={'rcfile': '--rcfile=${value}'},
            result_creator=create_pylint_result
        )

        runner.main()

        expected_task = Task(
            'Pylint module.py',
            'pylint -f parseable {}'.format(git.abspath('module.py')),
            create_pylint_result,
            pylint_config
        )
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher([expected_task])
        )

    def test_each_file_match_most_specific_pattern(self):
        """For each file only checkers from one pattern should be created"""
        accepted_code_rate = 9
        pylint_config = {
            'rcfile': None,
            'accepted-code-rate': accepted_code_rate
        }
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {
                '*.py': ['pylint'],
                'tests/*.py': ['pep8']
            }
        })

        staged_files = ['module.py',
                        'tests/module2.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pylint',
            taskname='Pylint ${file_relpath}',
            command='pylint -f parseable ${file_abspath} ${options}',
            defaultconfig=pylint_config,
            command_options={'rcfile': '--rcfile=${value}'}
        )
        patch_file_checker(
            'pep8',
            taskname='PEP8 ${file_relpath}',
            command='pep8 ${file_abspath}'
        )

        runner.main()

        expected_pylintchecker = Task(
            'Pylint module.py',
            'pylint -f parseable {}'.format(git.abspath('module.py')),
            create_result_by_returncode,
            pylint_config
        )
        expected_pep8_checker = Task(
            'PEP8 {}'.format('tests/module2.py'),
            'pep8 {}'.format(git.abspath('tests/module2.py')),
            create_result_by_returncode
        )
        expected_checkers = [expected_pylintchecker, expected_pep8_checker]
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )

    def test_file_checker_can_be_run_with_custom_config(self):
        """Config passed after file pattern should replace global one."""
        accepted_code_rate = 8
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pylint']},
            'config': {
                'pylint': {'accepted-code-rate': accepted_code_rate}
            }
        })
        staged_files = ['module.py',
                        'module2.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pylint',
            taskname='Pylint ${file_relpath}',
            command='pylint -f parseable ${file_abspath} ${options}',
            defaultconfig={
                'rcfile': None,
                'accepted-code-rate': 9
            },
            command_options={'rcfile': '--rcfile=${value}'}
        )

        runner.main()

        expected_checkers = []
        for each_file in staged_files:
            task = Task(
                'Pylint {}'.format(each_file),
                'pylint -f parseable {}'.format(git.abspath(each_file)),
                create_result_by_returncode,
                config={
                    'rcfile': None,
                    'accepted-code-rate': accepted_code_rate
                }
            )
            expected_checkers.append(task)
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )

    def test_config_can_be_set_for_file_pattern(self):
        """Local configuration options should not affect to global config."""
        global_acceptedcoderate = 9
        local_acceptedcoderate = 7
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {
                '*.py': ['pylint'],
                'tests/*.py': [{'pylint': {
                    'accepted-code-rate': local_acceptedcoderate
                }}]
            },
            'config': {
                'pylint': {'accepted-code-rate': global_acceptedcoderate}
            }
        })
        staged_files = ['module.py', 'tests/module.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pylint',
            taskname='Pylint ${file_relpath}',
            command='pylint -f parseable ${file_abspath} ${options}',
            defaultconfig={
                'rcfile': None,
                'accepted-code-rate': global_acceptedcoderate
            },
            command_options={'rcfile': '--rcfile=${value}'}
        )

        runner.main()

        expected_checkers = []
        expected_checkers.append(
            Task(
                'Pylint {}'.format('module.py'),
                'pylint -f parseable {}'.format(git.abspath('module.py')),
                create_result_by_returncode,
                config={
                    'rcfile': None,
                    'accepted-code-rate': global_acceptedcoderate
                }
            )
        )
        expected_checkers.append(
            Task(
                'Pylint {}'.format('tests/module.py'),
                'pylint -f parseable {}'.format(git.abspath('tests/module.py')),
                create_result_by_returncode,
                config={
                    'rcfile': None,
                    'accepted-code-rate': local_acceptedcoderate
                }
            )
        )
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )

    def test_configuration_can_contain_additional_command_options(self):
        rcfile = 'tests/pylintrc'
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {
                'tests/*.py': [{'pylint': {'rcfile': rcfile}}]
            }
        })
        staged_files = ['tests/module.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pylint',
            taskname='Pylint ${file_relpath}',
            command='pylint -f parseable ${file_abspath} ${rcfile}',
            defaultconfig={
                'rcfile': None,
                'accepted-code-rate': 9
            },
            command_options={'rcfile': '--rcfile=${value}'}
        )

        runner.main()

        expected_checker = Task(
            'Pylint tests/module.py',
            'pylint -f parseable {abspath} --rcfile={rcfile}' \
                .format(abspath=git.abspath('tests/module.py'), rcfile=rcfile),
            create_result_by_returncode,
            config={
                'rcfile': rcfile,
                'accepted-code-rate': 9
            }
        )
        expected_checker.rcfile = 'tests/pylintrc'
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher([expected_checker])
        )

    def test_single_checker_does_not_need_to_be_wrapped_in_list(self):
        precommit_yaml_contents = yaml.dump({
            'project-checkers': 'unittest',
            'file-checkers': {
                '*.py': 'pep8'
            }
        })
        staged_files = ['module.py']
        self.patch_git_repository(precommit_yaml_contents, staged_files)
        patch_file_checker(
            'pep8',
            taskname='pep8',
            command='dummy',
        )
        patch_project_checker('unittest',
                              taskname='unittest',
                              command='dummy',
                              result_creator=create_result_by_returncode)

        runner.main()

        expected_unittestchecker = Task(
            'unittest',
            'dummy',
            create_result_by_returncode
        )
        expected_pep8checker = Task(
            'pep8',
            'dummy',
            create_result_by_returncode
        )
        expected_checkers = [expected_unittestchecker, expected_pep8checker]
        self.worker.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )

    def test_script_exit_status_is_1_if_checker_fail(self):
        """If checker fail script should exit with code 1"""
        self.worker.execute_checkers.return_value = 1
        precommit_yaml_contents = yaml.dump({
            'project-checkers': ['unittest']
        })
        self.patch_git_repository(precommit_yaml_contents)
        patch_project_checker('unittest',
                              taskname='python unittest',
                              command='python -m unittest discover .')

        with self.assertRaises(SystemExit) as context:
            runner.main()
        exc = context.exception
        self.assertEqual(1, exc.code,
                         'If checker fail script should exit with code 1')

    def patch_git_repository(self, precommit_yaml_contents,
                             staged_files=None):
        """Prepare fake git repository and chdir to git repo

        Create precommit-checkers.yml with passed test contents.
        If staged_files is is not empty then checkers acts as if these files
        was staged, otherwise empty git staging area is simulated."""

        repo_root = self.repo_root
        precommit_yaml_path = path.join(repo_root, 'precommit-checkers.yml')
        file_structure = {
            precommit_yaml_path: precommit_yaml_contents
        }
        self._create_file_structure(file_structure)
        os.chdir(self.repo_root)

        if staged_files is None:
            staged_files = []
        staged_files_patch = mock.patch.object(
            git,
            'get_staged_files',
            lambda: staged_files
        )
        abspath_patch = mock.patch.object(
            git,
            'abspath',
            lambda rel_path: path.join(self.repo_root, rel_path)
        )
        self.addCleanup(staged_files_patch.stop)
        self.addCleanup(abspath_patch.stop)
        staged_files_patch.start()
        abspath_patch.start()

def patch_file_checker(checkername, taskname=None, command=None,
                       defaultconfig=None, command_options=None,
                       result_creator=None):
    # pylint: disable=too-many-arguments
    FILE_CHECKERS[checkername] = _create_checker_spec(
        taskname,
        command,
        defaultconfig,
        command_options,
        result_creator
    )

def patch_project_checker(checkername, taskname=None,
                          command=None, defaultconfig=None,
                          command_options=None, result_creator=None):
    # pylint: disable=too-many-arguments
    PROJECT_CHECKERS[checkername] = _create_checker_spec(
        taskname,
        command,
        defaultconfig,
        command_options,
        result_creator
    )

def _create_checker_spec(taskname=None, command=None,
                         defaultconfig=None, command_options=None,
                         result_creator=None):
    # pylint: disable=too-many-arguments
    checker_spec = {}
    fields_map = {
        TASKNAME: taskname,
        COMMAND: command,
        DEFAULTCONFIG: defaultconfig,
        COMMAND_OPTIONS: command_options,
        RESULT_CREATOR: result_creator
    }
    for fieldname in fields_map:
        value = fields_map[fieldname]
        if value is None:
            continue
        checker_spec[fieldname] = value
    return checker_spec

def _is_tasks_equal(expected, actual):
    # pylint: disable=protected-access
    """Check is two Task objects are equal."""
    return isinstance(expected, Task) and \
        isinstance(actual, Task) and \
        expected.taskname == actual.taskname and \
        expected._build_command() == actual._build_command() and \
        expected.config == actual.config and \
        expected._result_creator == actual._result_creator


UnOrderedCollectionMatcher.register_equalityfunc(Task, _is_tasks_equal)
