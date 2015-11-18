"""Load checkers from yaml file"""
import yaml
from codechecker import job_processor
from codechecker import git
from codechecker.checker import ExitCodeChecker
from codechecker.checker import PylintChecker

DEFAULT_ACCEPTED_PYLINT_RATE = 9


def create_pylint_checkers():
    """Create pylint checkers for all staged .py files"""
    staged_py_files = [f for f in git.get_staged_files() if f.endswith('.py')]
    return [PylintChecker(f, DEFAULT_ACCEPTED_PYLINT_RATE)
            for f in staged_py_files]

CHECKER_NAME_TO_CHECKER_FACTORY_MAP = {
    'unittest': lambda: ExitCodeChecker('python3 -m unittest discover .',
                                        'python unittest'),
    'pylint': create_pylint_checkers
}


def main():
    checkers = []
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))
    for checker_name in checkers_data:
        try:
            factory = CHECKER_NAME_TO_CHECKER_FACTORY_MAP[checker_name]
        except IndexError:
            raise RuntimeError(
                'Invalid checker name {}. Fix your precommit-checkers.yml'
                .format(checker_name))
        checker = factory()
        if isinstance(checker, list):
            checkers.extend(checker)
        else:
            checkers.append(checker)

    job_processor.process_jobs(checkers)
