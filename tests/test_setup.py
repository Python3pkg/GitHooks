import os
from os import path
import unittest
import fake_filesystem_unittest
import codechecker.setup

class SetupTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
         self.setUpPyfakefs()

    def test_setup_creates_scripts_with_proper_permissions(self):
        repository_root = '/path/to/repo'
        self._create_file_structure(repository_root)

        os.chdir(path.join(repository_root, 'dir1'))
        codechecker.setup.main()

        precommit_file_path = path.join(repository_root, '.git/hooks/pre-commit')
        precommit_checks_path = path.join(repository_root, 'precommit_checks.py')
        self.assertTrue(os.path.isfile(precommit_checks_path),
            'setup-githook should create precommit_checks.py file')
        self.assertTrue(os.path.isfile(precommit_file_path),
            'setup-githook should create .git/hooks/pre-commit file')
        self.assertTrue(os.access(precommit_checks_path, os.X_OK),
            'precommit_checks.py should be executable')
        self.assertTrue(os.access(precommit_file_path, os.X_OK),
            '.git/hooks/pre-commit should be executable')

    def _create_file_structure(self, repository_root):
        """Create all required files an directories"""
        file_structure = {
            '.git/hooks': {},
            'dir1': {},
            codechecker.setup.get_default_checks_path(): ''
        }
        os.makedirs(repository_root)
        for file_path, contents in file_structure.items():
            abs_path = path.join(repository_root, file_path)
            if isinstance(contents, str):
                self.fs.CreateFile(abs_path, contents=contents)
            elif isinstance(contents, dict):
                os.makedirs(abs_path)
