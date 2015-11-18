"""Yaml loader test cases"""
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


@mock.patch('codechecker.loader.job_processor', autospec=True)
class LoaderTestCase(TestCase):
    """Test cases for yaml loader"""

    def setUp(self):
        """Create virtual file structure"""
        self.setUpPyfakefs()
        self.repository_root = '/path/to/repository'

    def test_loader_executes_checkers_listed_in_config(self, job_processor):
        """For unittest code checker proper ExitCodeChecker is created"""
        yaml_contents = yaml.dump({
            'checkers': ['unittest']
        })
        self._create_files(yaml_contents)

        os.chdir(self.repository_root)
        loader.main()

        expected_command = 'python3 -m unittest discover .'
        expected_task_name = 'python unittest'
        expected = Matcher([ExitCodeChecker(expected_command,
                                            expected_task_name)])
        job_processor.process_jobs.assert_called_once_with(expected)

    @mock.patch('codechecker.loader.git', autospec=True)
    def test_pylint_checker_is_created_for_every_stashed_file(self, git,
                                                              job_processor):
        yaml_contents = yaml.dump({
            'checkers': ['pylint']
        })
        self._create_files(yaml_contents)
        modified_files = ['/path/to/repository/module.py',
                          '/path/to/repository/module2.py']
        git.get_staged_files.return_value = modified_files

        os.chdir(self.repository_root)
        loader.main()

        expected_checkers = []
        for modified_file_current in modified_files:
            expected_checkers.append(Matcher(PylintChecker(
                modified_file_current,
                loader.PylintCheckerFactory
                .default_config['accepted_code_rate'])))
        job_processor.process_jobs.assert_called_once_with(expected_checkers)

    @mock.patch('codechecker.loader.git', autospec=True)
    def test_pylint_checker_can_be_run_with_custom_config(self, git,
                                                          job_processor):
        accepted_code_rate = 8
        yaml_contents = yaml.dump({
            'checkers': ['pylint'],
            'config': {
                'pylint': {'accepted_code_rate': accepted_code_rate}
            }
        })
        self._create_files(yaml_contents)
        modified_files = ['/path/to/repository/module.py',
                          '/path/to/repository/module2.py']
        git.get_staged_files.return_value = modified_files

        os.chdir(self.repository_root)
        loader.main()

        expected_checkers = []
        for modified_file_current in modified_files:
            expected_checkers.append(Matcher(PylintChecker(
                modified_file_current, accepted_code_rate)))
        job_processor.process_jobs.assert_called_once_with(expected_checkers)

    def _create_files(self, yaml_contents):
        """Create all required files and directories"""
        repo_root = self.repository_root
        file_structure = {
            path.join(repo_root, 'precommit-checkers.yml'): yaml_contents
        }
        self._create_file_structure(file_structure)


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
    # pylint: disable=W1504
    # pylint: disable=W0212
    if not type(expected) == type(actual):
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
    # pylint: disable=W1504
    # pylint: disable=W0212
    if not type(expected) == type(actual):
        return 'Both compared objects should be PylintChecker. {}, {} given'\
            .format(context.label('x', repr(type(expected))),
                    context.label('y', repr(type(actual))))
    errors = []
    if expected.file_name != actual.file_name:
        errors.append('File names are not equal: {} !=  {}'.format(
            context.label('x', repr(expected.file_name)),
            context.label('y', repr(actual.file_name)),
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
