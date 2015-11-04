#!/usr/bin/env python3
"""Setup git pre-commit checks

Usage: setup-githook

This script must be executed in git repository or one of its
subdirectory. Creates two files with executable bit in repository
main directory:

* .git/hooks/pre-commit
* precommit_checks.py if does not exists yet

.git/hooks/pre-commit executes precommit_checks.py and exits with same
 status as precommit_checks.py

precommit_checks.py defines which checks should be executed before
commit
"""
import os
import stat
import shutil
from os import path
from string import Template
from pkg_resources import resource_filename


PRE_COMMIT_CODE_TPL = """python3 $precommit_checks_path;
exit $$?;
"""


def main():
    """Install pre-commit hook"""
    try:
        repo_dir = _find_repository_dir(os.getcwd())
    except GitRepoNotFoundError:
        print('Current working directory is not within a git repository.')
        exit(1)

    precommit_checks_filename = 'precommit_checks.py'

    precommit_path = path.join(repo_dir, '.git/hooks/pre-commit')
    precommit_file = open(precommit_path, 'w')
    precommit_file_tpl = Template(PRE_COMMIT_CODE_TPL)
    precommit_file.write(precommit_file_tpl.substitute(
        precommit_checks_path=precommit_checks_filename))
    precommit_file.close()
    precommit_stat = os.stat(precommit_path)
    os.chmod(precommit_path, precommit_stat.st_mode | stat.S_IEXEC)

    precommit_checks_dest = path.join(repo_dir, precommit_checks_filename)
    if not path.isfile(precommit_checks_dest):
        precommit_checks_src = get_default_checks_path()
        shutil.copyfile(precommit_checks_src, precommit_checks_dest)
        checker_stat = os.stat(precommit_checks_dest)
        os.chmod(precommit_checks_dest, checker_stat.st_mode | stat.S_IEXEC)


def get_default_checks_path():
    """Get path to default precommit_checks.py"""
    return resource_filename('codechecker', 'samples/precommit_checks.py')


def _find_repository_dir(curdir):
    """Get git repository path

    Traverse upwards from given directory until git repository is found

    :param curdir: directory path from which traversing begin
    :type curdir: string
    :returns: git directory path
    :rtype: string
    :raises: :exc:`GitRepoNotFoundError` if repository is not found
    """

    def is_git_repo(dir_path):
        """Check if passed path is git repository main directory"""
        return path.isdir(path.join(dir_path, '.git'))

    def is_root_dir(dir_path):
        """Check if passed path is root directory"""
        return dir_path == os.path.abspath(os.sep)

    curdir = path.abspath(curdir)
    while not is_root_dir(curdir):
        if is_git_repo(curdir):
            return curdir
        curdir = path.dirname(curdir)
    raise GitRepoNotFoundError('Git repository can not be found')


class GitRepoNotFoundError(RuntimeError):
    """Raised when git repository can not be found"""
    pass

if __name__ == '__main__':
    main()
