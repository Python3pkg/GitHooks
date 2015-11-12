import os
from os import path
import fake_filesystem_unittest
from unittest import mock
from codechecker import loader
from codechecker.checker import ExitCodeChecker

class LoaderTestCase(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.repository_root = '/path/to/repository'
        self._create_file_structure()

    @mock.patch('codechecker.loader.job_processor')
    def test_loader_executes_checkers_listed_in_config(self, job_processor):
        class Matcher:
            def __init__(self, expected):
                if len(expected) != 1:
                    raise ValueError('List of expected checkers'\
                                     ' should be one element list')
                self.expected = expected

            def __eq__(self, actual):
                expected = self.expected
                if len(expected) != len(actual):
                    return False
                for i, current_expected in enumerate(expected):
                    current_actual = actual[i]
                    if type(current_expected) != type(current_actual):
                        return False
                    if dir(current_expected) != dir(current_actual):
                        return False
                return True
        
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