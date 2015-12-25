"""Checker runner test cases"""
# pylint: disable=E1101
import os
from os import path
from unittest import mock
import yaml

from codechecker.scripts import runner
from codechecker.checker.base import (ExitCodeChecker,
                                      PylintChecker)
from codechecker import git
from codechecker.checker.builder import PylintCheckerFactory
from tests.testcase import TestCase
from tests.comparison import UnOrderedCollectionMatcher


class RunnerTestCase(TestCase):
    """Test cases for code checker runner

    This class test if code checker runner creates proper checkers with proper
    parameters for stashed files"""

    def setUp(self):
        """Create virtual file structure"""
        self.setUpPyfakefs()
        self.repo_root = '/path/to/repository'

        job_processor_patcher = mock.patch(
            'codechecker.scripts.runner.job_processor',
            autospec=True
        )
        self.addCleanup(job_processor_patcher.stop)
        self.job_processor = job_processor_patcher.start()
        self.job_processor.execute_checkers.return_value = 0

    def test_runner_unittest_checker_is_created_only_once(self):
        """For unittest code checker proper ExitCodeChecker is created"""
        precommit_yaml_contents = yaml.dump({
            'project-checkers': ['unittest']
        })
        self.setup_git_repository(precommit_yaml_contents)

        runner.main()

        expected_command = 'python -m unittest discover .'
        expected_task_name = 'python unittest'
        expected = UnOrderedCollectionMatcher(
            [ExitCodeChecker(expected_command, expected_task_name)]
        )
        self.job_processor.execute_checkers.assert_called_once_with(expected)

    def test_pep8_checker_is_created_for_every_stashed_file(self):
        """ExitCodeChecker can be created for staged files match pattern"""
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pep8']}
        })
        staged_files = ['module.py',
                        'module2.py']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        expected_checkers = []
        for file_path in staged_files:
            command = 'pep8 {}' \
                .format(path.join(self.repo_root, file_path))
            task_name = 'PEP8 {}'.format(file_path)
            expected_checkers.append(
                ExitCodeChecker(command, task_name)
            )
        expected_checkers = UnOrderedCollectionMatcher(expected_checkers)
        self.job_processor.execute_checkers \
            .assert_called_once_with(expected_checkers)

    def test_ExitCodeCheckerFactory_accepts_config(self):
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.js': ['jshint']},
            'config': {
                'jshint': {'command-options': '--config .jshintrc'}
            }
        })
        staged_files = ['module.js']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        expected_command = 'jshint --config .jshintrc' \
            ' /path/to/repository/module.js'
        expected_taskname = 'JSHint module.js'
        self.job_processor.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(
                [ExitCodeChecker(expected_command, expected_taskname)]
            )
        )

    def test_checker_is_created_for_every_stashed_file_matching_pattern(self):
        """Only files matching pattern should have created checkers"""
        accepted_code_rate = _get_default_acceptedcoderate()
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pylint']}
        })
        staged_files = ['module.py',
                        'module2.py',
                        'module.js']
        py_files = [f for f in staged_files if f.endswith('.py')]
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        self.assert_pylint_checkers_executed(py_files, accepted_code_rate)

    def test_each_file_match_most_specific_pattern(self):
        """For each file only checkers from one pattern should be created"""
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {
                '*.py': ['pylint'],
                'tests/*.py': ['pep8']
            }
        })
        staged_files = ['module.py',
                        'tests/module2.py']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        expected_pylintchecker = PylintChecker(
            'module.py',
            path.join(self.repo_root, 'module.py'),
            _get_default_acceptedcoderate()
        )
        expected_pep8_checker = ExitCodeChecker(
            'pep8 {}'.format(path.join(self.repo_root, 'tests/module2.py')),
            'PEP8 {}'.format('tests/module2.py')
        )
        expected_checkers = [expected_pylintchecker, expected_pep8_checker]
        self.job_processor.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )

    def test_file_checker_can_be_run_with_custom_config(self):
        accepted_code_rate = 8
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pylint']},
            'config': {
                'pylint': {'accepted_code_rate': accepted_code_rate}
            }
        })
        staged_files = ['module.py',
                        'module2.py']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        self.assert_pylint_checkers_executed(staged_files, accepted_code_rate)

    def test_config_can_be_set_for_file_pattern(self):
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {
                '*.py': ['pylint'],
                'tests/*.py': [{'pylint': {'accepted_code_rate': 7}}]
            },
            'config': {
                'pylint': {'accepted_code_rate': 8}
            }
        })
        staged_files = ['module.py',
                        'tests/module.py']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        accepted_code_rate = {
            'module.py': 8,
            'tests/module.py': 7
        }
        self.assert_pylint_checkers_executed(staged_files, accepted_code_rate)

    def test_pylintfactory_sets_additional_command_options_to_checker(self):
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {
                'tests/*.py': [{'pylint': {'rcfile': 'tests/pylintrc'}}]
            }
        })
        staged_files = ['tests/module.py']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        runner.main()

        expected_checker = PylintChecker(
            filename='tests/module.py',
            abspath=path.join(self.repo_root, 'tests/module.py'),
            accepted_code_rate=_get_default_acceptedcoderate()
        )
        expected_checker.rcfile = 'tests/pylintrc'
        self.job_processor.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher([expected_checker])
        )

    def test_script_exit_status_is_1_if_checker_fail(self):
        """If checker fail script should exit with code 1"""
        self.job_processor.execute_checkers.return_value = 1
        precommit_yaml_contents = yaml.dump({
            'project-checkers': ['unittest']
        })
        self.setup_git_repository(precommit_yaml_contents)

        with self.assertRaises(SystemExit) as context:
            runner.main()
        exc = context.exception
        self.assertEqual(1, exc.code,
                         'If checker fail script should exit with code 1')

    def setup_git_repository(self, precommit_yaml_contents,
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

    def assert_pylint_checkers_executed(self, files, accepted_code_rate):
        """Check if proper pylint checkers are sent to processing

        For every passed file pylint checker should be created with given
        accepted code rate and then sent to processing.

        :param files: list of files
        :param accepted_code_rate: if is dict then map every file to accepted
            code rate, otherwise if it is int then it is accepted code rate for
            all checkers
        :type accepted_code_rate: int or dict"""
        if isinstance(accepted_code_rate, int):
            all_accepted_coderate = {}
            for each_file in files:
                all_accepted_coderate[each_file] = accepted_code_rate
        else:
            all_accepted_coderate = accepted_code_rate

        expected_checkers = []
        for each_file in files:
            each_accepted_coderate = all_accepted_coderate[each_file]
            each_abspath = path.join(self.repo_root, each_file)
            each_checker = PylintChecker(
                filename=each_file,
                abspath=each_abspath,
                accepted_code_rate=each_accepted_coderate
            )
            expected_checkers.append(each_checker)
        self.job_processor.execute_checkers.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )


def _get_default_acceptedcoderate():
    """Get accepted code rate from PylintChecker config"""
    return PylintCheckerFactory.default_config['accepted_code_rate']


def _compare_pylint_checker(expected, actual):
    """Check if two PylintChecker objects are equal"""
    return isinstance(expected, PylintChecker) and \
        isinstance(actual, PylintChecker) and \
        expected.get_command() == actual.get_command() and \
        expected.get_taskname() == actual.get_taskname() and \
        expected.accepted_code_rate == actual.accepted_code_rate


def _compare_exitcode_checker(expected, actual):
    """Check if two ExitCodeChecker objects are equal"""
    # pylint: disable=protected-access
    return isinstance(expected, ExitCodeChecker) and \
        isinstance(actual, ExitCodeChecker) and \
        expected._command == actual._command and \
        expected._task_name == actual._task_name

UnOrderedCollectionMatcher.register_equalityfunc(PylintChecker,
                                                 _compare_pylint_checker)
UnOrderedCollectionMatcher.register_equalityfunc(ExitCodeChecker,
                                                 _compare_exitcode_checker)
