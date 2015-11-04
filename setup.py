# pylint: disable=C0111
# pylint: disable=C0103
from setuptools import setup
from os import path

project_dir = path.abspath(path.dirname(__file__))
with open(path.join(project_dir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='code-checker',
    version='0.1.0',
    description='Run pre-commit code checkers',
    long_description=long_description,
    url='https://github.com/droslaw/GitHooks',
    author='Sławek Dróżdż',
    author_email='droslaw@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Quality Assurance'
    ],
    packages=['codechecker'],
    include_package_data=True,
    package_data={'codechecker': ['samples/pre_commit_checks.py']},
    entry_points={
        'console_scripts': [
            'setup-githook = codechecker.setup:main',
        ],
    }
)
