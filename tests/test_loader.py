"""Yaml loader test cases"""
import os
from os import path
from unittest import mock
from testfixtures import compare
from testfixtures.comparison import register
from codechecker import loader
from codechecker.checker import ExitCodeChecker
from tests.testcase import TestCase


class LoaderTestCase(TestCase):
    """Test cases for yaml loader"""

    def setUp(self):
        """Create virtual file structure"""
        self.setUpPyfakefs()
        self.repository_root = '/path/to/repository'
        self._create_files()

    @mock.patch('codechecker.loader.job_processor')
    def test_loader_executes_checkers_listed_in_config(self, job_processor):
        """For unittest code checker proper ExitCodeChecker is created"""
        os.chdir(self.repository_root)
        loader.main()

        expected_command = 'python3 -m unittest discover .'
        expected_task_name = 'python unittest'
        expected = Matcher([ExitCodeChecker(expected_command,
                                            expected_task_name)])
        job_processor.process_jobs.assert_called_once_with(expected)

    def _create_files(self):
        """Create all required files and directories"""
        yaml_contents = """- unittest"""
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

register(ExitCodeChecker, compare_exitcode_checker)
