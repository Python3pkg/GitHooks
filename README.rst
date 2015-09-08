GitHooks
========
This script does any number of checks like unittests or pylint checks before git commit.
If at least one check will not pass, commit is aborted. 

Checks are treated as jobs divided among couple of workers.
Number of workers is equal to number of your cpu logical cores, every worker is executed in separate process.

Some checks are performed on whole project (unittest), other checks are performed on every file (e.g. pylint).
Only files added to git staging area are taken into account during jobs creation.

.. image:: https://cloud.githubusercontent.com/assets/898669/9682173/74cb7642-5304-11e5-8138-22cf50691879.png

See `Currently supported checkers`_

See `run_pre_commit_hook.py
<https://github.com/droslaw/GitHooks/blob/master/run_pre_commit_hook.py>`_ for example usage.

Installation
------------
1. ``cd $REPOSITORY_ROOT_DIR``
2. ``git submodule add git@github.com:droslaw/GitHooks.git``
3. ``cp GitHooks/run_pre_commit_hook.py ./``
4. ``cp GitHooks/pre-commit.sample .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit``

Make sure that every requirement of checkers (pylint, pep8 etc.) are installed in your system or active virtual environment.
You should install them manually.

Configuration
-------------
To customize pre-commit checking edit *run_pre_commit_hook.py* copied to parent repository.
Purpose of *run_pre_commit_hook.py* is to create checker jobs and send them to execution in last step.
In this file you can specify which checkers for which files will be created.

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