"""Load checkers from yaml file"""
import yaml
from codechecker import job_processor
from codechecker import git
from codechecker.checker import ExitCodeChecker
from codechecker.checker import PylintChecker
import copy


def main():
    checker_factory = CheckerFactoryDelegator()
    checker_factory.register_all_factories()
    checkers = []
    checkers_data = yaml.load(open('precommit-checkers.yml', 'r'))
    checkers_list = checkers_data['checkers']

    if 'config' in checkers_data:
        checkers_config = checkers_data['config']
        for checker_name, current_config in checkers_config.items():
            checker_factory.set_checker_config(checker_name, current_config)

    for checker_name in checkers_list:
        checker = checker_factory.create_checker(checker_name)
        if isinstance(checker, list):
            checkers.extend(checker)
        else:
            checkers.append(checker)

    job_processor.process_jobs(checkers)


class PylintCheckerFactory:
    """Handle PylintChecker creation"""

    default_config = {
        'accepted_code_rate': 9
    }

    def __init__(self):
        """Copy default configuration to instance"""
        self.config = copy.copy(self.default_config)

    def create(self):
        """Create pylint checker"""
        staged_py_files = [f for f in git.get_staged_files()
                           if f.endswith('.py')]
        accepted_code_rate = self.get_config_option('accepted_code_rate')
        return [PylintChecker(f, accepted_code_rate)
                for f in staged_py_files]

    def set_config(self, config):
        """Overwrite default configuration

        :type config: dict
        :raises: :exc:`ValueError` if passed config contains invalid option
        """
        for option_name, option_value in config.items():
            if option_name not in self.default_config:
                raise ValueError('{} is not valid option for pylint')
            self.config[option_name] = option_value

    def get_config_option(self, option_name):
        """Get config option from factory configuration"""
        return self.config[option_name]


class CheckerFactoryDelegator:
    """Delegate requests to proper checker factory

    Delegate requests (checker creation, setting config to checker factory)
    to proper factory
    """

    def __init__(self):
        self.factories = {}

    def create_checker(self, checker_name):
        """Create checker by passed checker name"""
        factory = self._get_checker_factory(checker_name)
        if callable(factory):
            return factory()
        else:
            return factory.create()

    def set_checker_config(self, checker_name, config):
        """Set config to factory corresponding to passed checker name"""
        factory = self._get_checker_factory(checker_name)
        factory.set_config(config)

    def register_factory(self, checker_name, factory):
        """Add checker factory to delegator"""
        self.factories[checker_name] = factory

    def register_all_factories(self):
        self.register_factory(
            'unittest',
            lambda: ExitCodeChecker('python3 -m unittest discover .',
                                    'python unittest')
        )
        self.register_factory(
            'pep8',
            lambda: [ExitCodeChecker('pep8 {}'.format(f), 'PEP8 {}:'.format(f))
                     for f in git.get_staged_files() if f.endswith('.py')]
        )
        self.register_factory('pylint', PylintCheckerFactory())

    def _get_checker_factory(self, checker_name):
        """Get checker factory by passed checker name"""
        try:
            factory = self.factories[checker_name]
        except KeyError:
            raise RuntimeError('Invalid checker name {}'.format(checker_name))
        return factory
