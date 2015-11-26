"""Yaml loader test cases"""
# pylint: disable=E1101
import os
from os import path
from unittest import mock
from testfixtures import compare
from testfixtures.comparison import register
import yaml
from codechecker import loader
from codechecker.checker import ExitCodeChecker
from codechecker.checker import PylintChecker
from tests.testcase import TestCase


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
        expected = Matcher([ExitCodeChecker(expected_command,
                                            expected_task_name)])
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
        expected_checkers = Matcher(expected_checkers)
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
            Matcher([ExitCodeChecker(expected_command, expected_taskname)])
        )

    def test_checker_is_created_for_every_stashed_file_matching_pattern(self):
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

        self.assert_pylint_checkers_processed(py_files, accepted_code_rate)

    def test_sort_file_patterns(self):
        unsorted_patterns = ['*.py', 'tests/*.py']
        sorted_patterns = ['tests/*.py', '*.py']

        self.assertEqual(sorted_patterns,
                         loader._sort_file_patterns(unsorted_patterns))

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

        self.assert_pylint_checkers_processed(staged_files, accepted_code_rate)

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

    def assert_pylint_checkers_processed(self, files, accepted_code_rate):
        """Check if proper pylint checkers are sent to processing

        For every passed file pylint checker should be created with given
        accepted code rate and then sent to processing."""
        expected_checkers = []
        for each_file in files:
            each_checker = PylintChecker(each_file, accepted_code_rate)
            each_checker.set_abspath(path.join(self.repo_root, each_file))
            expected_checkers.append(each_checker)
        self.job_processor.process_jobs.assert_called_once_with(
            Matcher(expected_checkers)
        )


class Matcher:
    # pylint: disable=R0903
    """Compare two objects using :py:func:`testfixtures.comparison.compare`"""

    def __init__(self, expected):
        """Set expected value"""
        self.expected = expected

    def __eq__(self, actual):
        """Compare passed value to expected one"""
        compare(self.expected, actual)
        return True


def compare_exitcode_checker(expected, actual, context):
    """Compare :class:`codechecker.checker.ExitCodeChecker` objects

    :param expected: first object to compare
    :type expected: codechecker.checker.ExitCodeChecker
    :param actual: second object to compare
    :type actual: codechecker.checker.ExitCodeChecker
    :type context: testfixtures.comparison.CompareContext
    :returns: None if objects are equal otherwise differences description
    :rtype: None or string
    :raises: :exc:`AssertionError`
    """
    # pylint: disable=W0212
    if not isinstance(expected, ExitCodeChecker)\
            or not isinstance(actual, ExitCodeChecker):
        return 'Both compared objects should be ExitCodeChecker. {}, {} given'\
            .format(context.label('x', repr(type(expected))),
                    context.label('y', repr(type(actual))))
    errors = []
    if expected._command != actual._command:
        errors.append('Commands are not equal: {} !=  {}'.format(
            context.label('x', repr(expected._command)),
            context.label('y', repr(actual._command)),
        ))
    if expected._task_name != actual._task_name:
        errors.append('Task names are not equal:  {} !=  {}'.format(
            context.label('x', repr(expected._task_name)),
            context.label('y', repr(actual._task_name)),
        ))
    if errors:
        return '\n'.join(errors)
    return None


def compare_pylint_checker(expected, actual, context):
    """Compare :class:`codechecker.checker.PylintChecker` objects

    :param expected: first object to compare
    :type expected: codechecker.checker.PylintChecker
    :param actual: second object to compare
    :type actual: codechecker.checker.PylintChecker
    :type context: testfixtures.comparison.CompareContext
    :returns: None if objects are equal otherwise differences description
    :rtype: None or string
    :raises: :exc:`AssertionError`
    """
    # pylint: disable=W0212
    if not isinstance(expected, PylintChecker)\
            or not isinstance(actual, PylintChecker):
        return 'Both compared objects should be PylintChecker. {}, {} given'\
            .format(context.label('x', repr(type(expected))),
                    context.label('y', repr(type(actual))))
    errors = []
    if expected.get_command() != actual.get_command():
        errors.append('Commands are not equal: {} !=  {}'.format(
            context.label('x', repr(expected.get_command())),
            context.label('y', repr(actual.get_command())),
        ))
    if expected.get_taskname() != actual.get_taskname():
        errors.append('Task names are not equal: {} !=  {}'.format(
            context.label('x', repr(expected.get_taskname())),
            context.label('y', repr(actual.get_taskname())),
        ))
    if expected.accepted_code_rate != actual.accepted_code_rate:
        errors.append('Accepted code rates are not equal:  {} !=  {}'.format(
            context.label('x', repr(expected.accepted_code_rate)),
            context.label('y', repr(actual.accepted_code_rate)),
        ))
    if errors:
        return '\n'.join(errors)
    return None

register(ExitCodeChecker, compare_exitcode_checker)
register(PylintChecker, compare_pylint_checker)
