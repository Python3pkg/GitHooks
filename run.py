#!/usr/bin/env python3
import re
import multiprocessing as mp
from subprocess import Popen, PIPE

WORKERS_COUNT = mp.cpu_count()

class CheckResult:
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'

    def __init__(self, task_name, status=SUCCESS):
        self.task_name = task_name
        self.status = status
        self.summary = ''
        self.info = ''
        self.message = ''

def error(text):
    return '\033[1m\033[31m{text}\033[0m'.format(text=text)

def success(text):
    return '\033[1m\033[32m{text}\033[0m'.format(text=text)

def warning(text):
    return '\033[1m\033[33m{text}\033[0m'.format(text=text)

def info(text):
    return '\033[1m\033[34m{text}\033[0m'.format(text=text)

def bold(text):
    return '\033[1m{text}\033[0m'.format(text=text)

DEFAULT_SUMMARY_TEXT = {
    CheckResult.SUCCESS: 'OK',
    CheckResult.WARNING: 'OK',
    CheckResult.ERROR: 'FAILED'
}

SUMMARY_FORMAT = {
    CheckResult.SUCCESS: success,
    CheckResult.WARNING: warning,
    CheckResult.ERROR: error
}

def print_result(result):
    if result.summary:
        summary = result.summary
    else:
        summary = DEFAULT_SUMMARY_TEXT[result.status]
    summary = SUMMARY_FORMAT[result.status](summary)
    task_name = bold(result.task_name)
    print('* {task}: {summary}'.format(task=task_name, summary=summary))
    if result.info:
        print(info(result.info))
    if result.message:
        print(result.message)


def get_staged_files():
    git_args = 'git diff --staged --name-only'.split()
    git_process = Popen(git_args, stdout=PIPE)
    git_process.wait()

    # Filter deleted files
    file_list = [f for f in [f.strip().decode(sys.stdout.encoding)
                             for f in git_process.stdout.readlines()]\
                    if os.path.exists(f) or True]
    return file_list

def run_unittest():
    test_args = 'python3 -m unittest discover .'.split()
    test_process = Popen(test_args, stdout=PIPE, stderr=PIPE)
    test_process.wait()
    tests_output = test_process.stderr.read().decode(sys.stdout.encoding)

    result = CheckResult('Running python unittest')
    if not tests_output.endswith('OK\n'):
        result.status = CheckResult.ERROR
        result.message = tests_output
    return result

class PylintCheck:
    ACCEPTED_PYLINT_RATE = 9
    RE_CODE_RATE = re.compile(r'Your code has been rated at ([\d\.]+)/10')
    RE_PYLINT_MESSAGE = re.compile(r'^([a-zA-Z1-9_/]+\.py:\d+:.+)$', re.MULTILINE)

    def __init__(self, file_name):
        self.file_name = file_name

    def __call__(self):
        pylint_args = 'pylint -f parseable {}'.format(self.file_name).split()
        pylint_process = Popen(pylint_args, stdout=PIPE, stderr=PIPE)
        pylint_process.wait()
        pylint_output = pylint_process.stdout.read().decode(sys.stdout.encoding)

        current_rate = float(self.RE_CODE_RATE.findall(pylint_output)[0])

        result = CheckResult('Checking file {} by pylint'.format(self.file_name))

        if current_rate == 10:
            return result

        messages = '\n'.join(self.RE_PYLINT_MESSAGE.findall(pylint_output))
        if current_rate >= self.ACCEPTED_PYLINT_RATE:
            result.status = CheckResult.WARNING
            result.summary = 'Code Rate {}/10'.format(current_rate)
        else:
            result.status = CheckResult.ERROR
            result.summary = 'Failed: Code Rate {}/10'.format(current_rate)
        result.message = messages

        return result

if __name__ == '__main__':
    import os
    import sys

    # Prepare files
    file_list = get_staged_files()
    py_files = [f for f in file_list if f.endswith('.py')]
    # Exclude test cases
    py_files = [f for f in py_files if not os.path.basename(f).startswith('test_')]

    # Add jobs
    jobs = []
    jobs.append(run_unittest)
    for file_name in py_files:
        jobs.append(PylintCheck(file_name))

    # Prepare workers and process jobs
    pool = mp.Pool(processes=WORKERS_COUNT)
    results = [pool.apply_async(job) for job in jobs]

    # Check results
    is_ok = True
    for result in results:
        result = result.get()
        print_result(result)
        if not result.status == CheckResult.ERROR:
            is_ok = False
    print('-' * 80)
    if is_ok:
        print(success('OK'))
    else:
        print(error('Commit aborted'))

    if is_ok:
        sys.exit(0)
    else:
        sys.exit(1)
