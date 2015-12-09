"""Function for inspecting git repo"""
import os
from os import path
import sys
from subprocess import Popen, PIPE


def find_repository_dir(curdir):
    """Get git repository main directory path

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
        return dir_path == path.abspath(os.sep)

    curdir = path.abspath(curdir)
    while not is_root_dir(curdir):
        if is_git_repo(curdir):
            return curdir
        curdir = path.dirname(curdir)
    raise GitRepoNotFoundError('Git repository can not be found')

_REPOSITORY_DIR_PATH = find_repository_dir(os.getcwd())


def abspath(rel_path):
    """Get absolute path

    Convert relative path to absolute one. Passed path must be relative to
    git repository main directory"""
    return path.join(_REPOSITORY_DIR_PATH, rel_path)


def get_staged_files():
    """Return files in git staging area"""
    def normpath(file_relpath):
        """Get absolute path"""
        return file_relpath
        return path.join(repository_path, file_relpath)
    repository_path = find_repository_dir(os.getcwd())
    git_args = 'git diff --staged --name-only'.split()
    git_process = Popen(git_args, stdout=PIPE)
    git_process.wait()

    # read staged files and filter deleted ones
    file_list = [f for f in [normpath(f.decode(sys.stdout.encoding).strip())
                             for f in git_process.stdout.readlines()]
                 if os.path.exists(f)]
    return file_list


class GitRepoNotFoundError(RuntimeError):
    """Raised when git repository can not be found"""
    pass
