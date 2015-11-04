import os
import sys
from subprocess import Popen, PIPE


def get_staged_files():
    """Return files in git staging area"""
    git_args = 'git diff --staged --name-only'.split()
    git_process = Popen(git_args, stdout=PIPE)
    git_process.wait()

    # Filter deleted files
    file_list = [f for f in [f.strip().decode(sys.stdout.encoding)
                             for f in git_process.stdout.readlines()]
                 if os.path.exists(f)]
    return file_list
