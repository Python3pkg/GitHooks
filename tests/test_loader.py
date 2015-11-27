"""Yaml loader test cases"""
# pylint: disable=E1101
import os
from os import path
from unittest import mock
import yaml

from codechecker import loader
from codechecker.checker import (ExitCodeChecker,
                                 PylintChecker)
from tests.testcase import TestCase
from tests.comparison import UnOrderedCollectionMatcher


class LoaderTestCase(TestCase):
    """Test cases for yaml loader"""

    def setUp(self):
        """Create virtual file structure"""
        self.setUpPyfakefs()
        self.repo_root = '/path/to/repository'

        job_processor_patcher = mock.patch('codechecker.loader.job_processor',
                                           autospec=True)
        self.addCleanup(job_processor_patcher.stop)
        self.job_processor = job_processor_patcher.start()

    def test_loader_unittest_checker_is_created_only_once(self):
        """For unittest code checker proper ExitCodeChecker is created"""
        precommit_yaml_contents = yaml.dump({
            'project-checkers': ['unittest']
        })
        self.setup_git_repository(precommit_yaml_contents)

        loader.main()

        expected_command = 'python3 -m unittest discover .'
        expected_task_name = 'python unittest'
        expected = UnOrderedCollectionMatcher(
            [ExitCodeChecker(expected_command, expected_task_name)]
        )
        self.job_processor.process_jobs.assert_called_once_with(expected)

    def test_pep8_checker_is_created_for_every_stashed_file(self):
        """ExitCodeChecker can be created for staged files match pattern"""
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pep8']}
        })
        staged_files = ['module.py',
                        'module2.py']
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        loader.main()

        expected_checkers = []
        for file_path in staged_files:
            command = 'pep8 {}' \
                .format(path.join(self.repo_root, file_path))
            task_name = 'PEP8 {}:'.format(file_path)
            expected_checkers.append(
                ExitCodeChecker(command, task_name)
            )
        expected_checkers = UnOrderedCollectionMatcher(expected_checkers)
        self.job_processor.process_jobs \
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

        loader.main()

        expected_command = 'jshint --config .jshintrc' \
            ' /path/to/repository/module.js'
        expected_taskname = 'JSHint module.js:'
        self.job_processor.process_jobs.assert_called_once_with(
            UnOrderedCollectionMatcher(
                [ExitCodeChecker(expected_command, expected_taskname)]
            )
        )

    def test_checker_is_created_for_every_stashed_file_matching_pattern(self):
        """Only files matching pattern should have created checkers"""
        accepted_code_rate = loader.PylintCheckerFactory \
            .default_config['accepted_code_rate']
        precommit_yaml_contents = yaml.dump({
            'file-checkers': {'*.py': ['pylint']}
        })
        staged_files = ['module.py',
                        'module2.py',
                        'module.js']
        py_files = [f for f in staged_files if f.endswith('.py')]
        self.setup_git_repository(precommit_yaml_contents, staged_files)

        loader.main()

        self.assert_pylint_checkers_executed(py_files, accepted_code_rate)

    def test_sort_file_patterns(self):
        unsorted_patterns = ['*.py', 'tests/*.py']
        sorted_patterns = ['tests/*.py', '*.py']

        self.assertEqual(sorted_patterns,
                         loader.sort_file_patterns(unsorted_patterns))

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

        loader.main()

        self.assert_pylint_checkers_executed(staged_files, accepted_code_rate)

    def setup_git_repository(self, precommit_yaml_contents,
                             staged_files=None):
        """Prepare git fake git repository and chdir to git repo

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
        git_patcher = mock.patch('codechecker.loader.git', autospec=True)
        self.addCleanup(git_patcher.stop)
        git_mock = git_patcher.start()
        git_mock.get_staged_files.return_value = staged_files
        git_mock.abspath.side_effect = \
            lambda rel_path: path.join(self.repo_root, rel_path)

    def assert_pylint_checkers_executed(self, files, accepted_code_rate):
        """Check if proper pylint checkers are sent to processing

        For every passed file pylint checker should be created with given
        accepted code rate and then sent to processing."""
        expected_checkers = []
        for each_file in files:
            each_checker = PylintChecker(each_file, accepted_code_rate)
            each_checker.set_abspath(path.join(self.repo_root, each_file))
            expected_checkers.append(each_checker)
        self.job_processor.process_jobs.assert_called_once_with(
            UnOrderedCollectionMatcher(expected_checkers)
        )


def _compare_pylint_checker(expected, actual):
    """Check if two PylintChecker objects are equal"""
    return isinstance(expected, PylintChecker) and \
        isinstance(actual, PylintChecker) and \
        expected.get_command() == actual.get_command() and \
        expected.get_taskname() == actual.get_taskname()


def _compare_exitcode_checker(expected, actual):
    """Check if two ExitCodeChecker objects are equal"""
    # pylint: disable=W0212
    return isinstance(expected, ExitCodeChecker) and \
        isinstance(actual, ExitCodeChecker) and \
        expected._command == actual._command and \
        expected._task_name == actual._task_name

UnOrderedCollectionMatcher.register_equalityfunc(PylintChecker,
                                                 _compare_pylint_checker)
UnOrderedCollectionMatcher.register_equalityfunc(ExitCodeChecker,
                                                 _compare_exitcode_checker)
