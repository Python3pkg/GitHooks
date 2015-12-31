"""Test installation of pre-commit hook"""
import os
from os import path
from tests.testcases.scripts.fakefs_testcase import FakeFSTestCase

from codechecker.scripts import hooksetup as setup


class TestHookSetup(FakeFSTestCase):
    """Test installation of pre-commit hook"""
    def setUp(self):
        self.setUpPyfakefs()
        self.repo_path = '/path/to/repo'

    def test_setup_creates_precommit_hook(self):
        git_hooks_dir = path.join(self.repo_path, '.git/hooks/')
        subdir = path.join(self.repo_path, 'subdir')
        files_structure = {
            git_hooks_dir: {},
            subdir: {}
        }
        self._create_file_structure(files_structure)
        os.chdir(subdir)
        setup.main()

        precommit_hook_path = path.join(self.repo_path,
                                        '.git/hooks/pre-commit')
        checker_config_path = path.join(self.repo_path,
                                        'precommit-checkers.yml')
        self.assertTrue(
            path.isfile(precommit_hook_path),
            'setup-githook should create .git/hooks/pre-commit file'
        )
        self.assertTrue(
            path.isfile(checker_config_path),
            'setup-githook should create precommit-checkers.yml file'
        )
        self.assertTrue(
            os.access(precommit_hook_path, os.X_OK),
            '.git/hooks/pre-commit should be executable'
        )
        precommit_hook_contents = open(precommit_hook_path).read()
        self.assertEqual(PRECOMMIT_HOOK_EXPECTED, precommit_hook_contents,
                         'Created pre-commit hook has invalid content')

    def test_setup_does_not_override_existing_checker_config(self):
        git_hooks_dir = path.join(self.repo_path, '.git/hooks/')
        checkers_conf_path = path.join(self.repo_path,
                                       'precommit-checkers.yml')
        checkers_conf_contents = 'This is important data'
        files_structure = {
            git_hooks_dir: {},
            checkers_conf_path: checkers_conf_contents
        }
        self._create_file_structure(files_structure)
        os.chdir(self.repo_path)

        setup.main()

        checkers_conf_actual = open(checkers_conf_path).read()
        self.assertEqual(checkers_conf_contents, checkers_conf_actual,
                         'setup-githook should not override existing'
                         ' precommit-checkers.yml')


    def test_setup_does_not_override_existing_hooks(self):
        precommit_hook_path = path.join(self.repo_path,
                                        '.git/hooks/pre-commit')
        files_structure = {
            precommit_hook_path: 'check-code',
        }
        self._create_file_structure(files_structure)
        os.chdir(self.repo_path)
        self.assertRaises(RuntimeError, setup.main)


PRECOMMIT_HOOK_EXPECTED = """check-code;
exit $?;"""