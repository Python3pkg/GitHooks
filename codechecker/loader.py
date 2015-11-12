"""Load checkers from yaml file"""
import yaml
from codechecker import job_processor
from codechecker.checker import ExitCodeChecker


def main():
    checkers = []
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))
    for checker in checkers_data:
        if checker == 'unittest':
            checkers.append(ExitCodeChecker('python3 -m unittest discover .',
                                            'python unittest'))

    job_processor.process_jobs(checkers)
