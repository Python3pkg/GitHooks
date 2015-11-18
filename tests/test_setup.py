"""Pre-commit commit checker installator tests"""
import os
from os import path
import codechecker.setup
from tests.testcase import TestCase


class SetupTest(TestCase):
    """Pre-commit commit checker installator test cases"""

    def setUp(self):
        """Prepare pyfakefs"""
        self.setUpPyfakefs()

    def test_setup_creates_scripts_with_proper_permissions(self):
        """Test pre-commit scripts creation"""
        repository_root = '/path/to/repo'
        self._prepare_filesystem(repository_root)

        os.chdir(path.join(repository_root, 'dir1'))
        codechecker.setup.main()

        precommit_file_path = path.join(repository_root,
                                        '.git/hooks/pre-commit')
        precommit_checks_path = path.join(repository_root,
                                          'precommit_checks.py')
        self.assertTrue(
            os.path.isfile(precommit_checks_path),
            'setup-githook should create precommit_checks.py file')
        self.assertTrue(
            os.path.isfile(precommit_file_path),
            'setup-githook should create .git/hooks/pre-commit file')
        self.assertTrue(
            os.access(precommit_checks_path, os.X_OK),
            'precommit_checks.py should be executable')
        self.assertTrue(
            os.access(precommit_file_path, os.X_OK),
            '.git/hooks/pre-commit should be executable')

    def _prepare_filesystem(self, repository_root):
        """Create all required files an directories"""
        file_structure = {
            path.join(repository_root, '.git/hooks'): {},
            path.join(repository_root, 'dir1'): {},
            codechecker.setup.get_default_checks_path(): ''
        }
        self._create_file_structure(file_structure)
