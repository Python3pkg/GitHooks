code-checker
============

This app does any number of checks such as unittests or pylint before git commit.
If at least one check will not pass, commit is aborted. 

.. image:: https://cloud.githubusercontent.com/assets/898669/10948860/0dcede00-8330-11e5-8b14-5490c4a00d57.png

.. image:: https://cloud.githubusercontent.com/assets/898669/10948864/16ba38b6-8330-11e5-85b8-02bb0332105b.png

To use *code-checker* in your project execute command `setup-githook`. This command
creates git pre-commit hook (.git/hooks/pre-commit) and precommit_checks.py listed below.

.. code-block:: python

   import os
   import sys
   from codechecker.checker import PylintChecker
   from codechecker.checker import ExitCodeChecker
   from codechecker import job_processor
   from codechecker import helper
   
   ACCEPTED_PYLINT_RATE = 9
   
   # Execute checks only on files added to git staging area
   file_list = helper.get_staged_files()
   
   py_files = [f for f in file_list if f.endswith('.py')]
   # Exclude test cases
   py_files = [f for f in py_files if not os.path.basename(f).startswith('test_')]
   
   # Add checkers
   checkers = []
   checkers.append(ExitCodeChecker('python3 -m unittest discover .',
                                   'python unittest'))
   for file_name in py_files:
       checkers.append(PylintChecker(file_name, ACCEPTED_PYLINT_RATE))
       checkers.append(ExitCodeChecker('pep8 {}'.format(file_name),
                                       'PEP8: {}'.format(file_name)))
   
   sys.exit(job_processor.process_jobs(checkers))

Above script executes unit tests for project and pylint along with pep8 for every `.py` file.

`precommit_checks.py` are separated from `.git/hooks/pre-commit` so
`precommit_checks.py` is under git version control.

Checks are treated as jobs divided among couple of workers.
Number of workers is equal to number of your cpu logical cores, every worker is executed in separate process.

See `Currently supported checkers`_

Installation
------------

.. code-block:: bash

   pip install code-checker

.. note::

   Installation of code-checker requires Python 3 and pip

Uninstallation
--------------

.. code-block:: bash

   pip uninstall code-checker

Git hooks setup
---------------

1. Change current working directory to git repository
   `cd /path/to/repository`

2. Execute `setup-githooks`. This command creates pre-commit hook
which run `precommit_checker.py` before commit

.. note::

   Make sure that every requirement of checkers (pylint, pep8 etc.) are installed in your system or active virtual environment.
   You should install them manually.

Customization
-------------

To customize pre-commit checking edit `precommit_checker.py`.

Currently supported checkers
----------------------------

**ExitCodeChecker**:

:Description:
  Run system shell command and fail if exit code is non 0

*Usage*:
Create ``ExitCodeChecker`` object with arguments:

1. command to execute (string)
2. task name displayed before result in console

.. code:: python

  # ...
  from checker import ExitCodeChecker
  # ...
  jobs = []
  # ...
  jobs.append(ExitCodeChecker('python3 -m unittest discover .',
                              'python unittest'))

*Example result:*
  ``* python unittest: OK``

**pylint**:

:Description:
  Check passes if pylint code rate for particular file is greather or equal to accepted code rate.
  Accepted code rate is 

:Requirements:
  pylint

*Usage*:

.. code:: python

  # ...
  from checker import PylintChecker
  # ...
  ACCEPTED_PYLINT_RATE = 9
  jobs = []
  # ...
  jobs.append(PylintChecker(file_name, ACCEPTED_PYLINT_RATE))