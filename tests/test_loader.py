"""Yaml loader test cases"""
import os
from os import path
import fake_filesystem_unittest
from unittest import mock
from testfixtures import compare
from testfixtures.comparison import register
from codechecker import loader
from codechecker.checker import ExitCodeChecker


class LoaderTestCase(fake_filesystem_unittest.TestCase):
    """Test cases for yaml loader"""

    def setUp(self):
        """Create virtual file structure"""
        self.setUpPyfakefs()
        self.repository_root = '/path/to/repository'
        self._create_file_structure()

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

    def _create_file_structure(self):
        """Create all required files and directories"""
        yaml_contents = """- unittest"""
        repository_root = self.repository_root
        file_structure = {
            'precommit-checkers.yml': yaml_contents
        }
        os.makedirs(repository_root)
        for file_path, contents in file_structure.items():
            abs_path = path.join(repository_root, file_path)
            if isinstance(contents, str):
                self.fs.CreateFile(abs_path, contents=contents)
            elif isinstance(contents, dict):
                os.makedirs(abs_path)


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
