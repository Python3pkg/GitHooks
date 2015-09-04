GitHooks
========
This script does any number of checks like unittests or pylint checks before git commit.
If at least one check will not pass, commit is aborted. 

Checks are treated as jobs divided among couple of workers.
Number of workers is equal to number of your cpu logical cores, every worker is executed in separate process.

Some checks are performed on whole project (unittest), other checks are performed on every file (e.g. pylint).
Only files added to git staging area are taken into account during jobs creation.

`Currently supported checkers`_

Installation
------------
1. ``cd $REPOSITORY_ROOT_DIR``
2. ``git submodule add git@github.com:droslaw/GitHooks.git``
3. ``cp GitHooks/run_pre_commit_hook.py ./``
4. ``cp GitHooks/pre-commit.sample .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit``

Make sure that every requirement of checkers (pylint, pep8) are installed in your system or active virtual environment.
You should install them manually.

Configuration
-------------
To customize pre-commit checking edit *run_pre_commit_hook.py* copied to parent repository.
Purpose of *run_pre_commit_hook.py* is to create checker jobs and send them to execution in last step.
In this file you can specify which checkers for which files will be created.

Currently supported checkers
----------------------------
**unittest**:

:Description:
  Run unittest by executing ``python3 -m unittest discover .``

:Requirements:
  unittest is part of The Python Standard Library

*Usage*:

Add ``checker.check_unittest`` function to jobs list in run_pre_commit_hook.py:

.. code:: python

  # ...
  from checker import check_unittest
  # ...
  jobs = []
  # ...
  jobs.append(check_unittest)

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

**pep8**:

:Description:
  Passes if pep8 tool does not return any message

:Requirements:
  pep8

*Usage*:

.. code:: python

  # ...
  from checker import PEP8Checker
  # ...
  jobs = []
  # ...
  jobs.append(PEP8Checker(file_name))
