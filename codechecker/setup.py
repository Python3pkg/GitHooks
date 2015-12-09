"""Setup git pre-commit hooks in repository"""
import os
import stat
from codechecker import git


def main():
    """Create pre-commit hook and checkers config

    - Create pre-commit hook, if pre-commit hook already exists raise exception
    - Create precommit-checkers.yml if does not exists yet
    """
    repo_dir = git.find_repository_dir(os.getcwd())
    precommit_hook_path = os.path.join(repo_dir, '.git/hooks/pre-commit')
    if os.path.isfile(precommit_hook_path):
        raise RuntimeError('".git/hooks/pre-commit" already exists'
                           ' Remove existing pre-commit hook'
                           ' if you want create new')
    hook_file = open(precommit_hook_path, 'w')
    hook_file.write(PRECOMMIT_HOOK_CONTENTS)
    hook_file.close()
    hook_file_stat = os.stat(precommit_hook_path)
    os.chmod(precommit_hook_path, hook_file_stat.st_mode | stat.S_IEXEC)

    checkers_config_path = os.path.join(repo_dir, 'precommit-checkers.yml')
    if not os.path.isfile(checkers_config_path):
        checkers_config = open(checkers_config_path, 'w')
        checkers_config.write('# Configure your checkers here')
        checkers_config.close()


PRECOMMIT_HOOK_CONTENTS = """check-code;
exit $?;"""
