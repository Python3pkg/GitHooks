code-checker
============

Intro
-----

This app does any number of checks such as unittests or lint during pre-commit check.
If at least one check will not pass, commit is aborted.

Checkers can be also run by command `check-code`.

Checkers are treated as jobs divided among couple of workers.
Number of workers is equal to number of your cpu logical cores, every worker is executed in separate process (on separate cpu core).

.. image:: https://cloud.githubusercontent.com/assets/898669/10948860/0dcede00-8330-11e5-8b14-5490c4a00d57.png

.. image:: https://cloud.githubusercontent.com/assets/898669/10948864/16ba38b6-8330-11e5-85b8-02bb0332105b.png

In `precommit-checkers.yml` you can configure which checkers checks which files and define checkers configuration. 

There are two categories of checkers: project-checkers and file-checker. 

Every project-checker is executed only once during pre-commit check. Example of project-checker is `unittest` - this checker is executed for whole project.

Every `file-checker` can be executed for every file in git staging area (git index). See examples below.

Currently supported checkers are:

- unittest:
   python unittest runner
- pylint
- pep8
- jshint

In near future more checkers will be added, especially for php and js.

precommit-checkers.yml Examples
-------------------------------

.. code-block:: yaml

   project-checkers: [unittest]
   file-checkers:
     '*.py': [pylint, pep8]
     '*.js': 'jshint'

If your `precommit-checkers.yml` is same as above, pre-commit check will execute python unittest for project, pylint and pep8 for *.py files and jshint for js files.

`pep8` and `jshint` checkers does not pass if at least one warning will occur. `pylint` does not pass if computed code rate is below `accepted_code_rate`, default `accepted_code_rate` is 9.

.. code-block:: yaml

   project-checkers: [unittest]
   file-checkers:
     '*.py': [pylint, pep8]
     '*.js': 'jshint'
   config: 
     pylint: {accepted_code_rate: 8}

This example shows how to set global configuration for specified checkers. Above configuration has similar effect as previous example but here accepted code rate computed by pylint is set to 8.

.. code-block:: yaml

   project-checkers: [unittest]
   file-checkers:
     '*.py': [pylint, pep8]
     'tests/*.py':
       - pylint: {accepted_code_rate: 8}
   config: 
     pylint: {accepted_code_rate: 9}

Checker options can be set also for specific file pattern. In this example python modules under `tests/` directory will be checked by `pylint` with accepted code rate 8. Rest of python modules will be checkek by `pep8` and `pylint` with accepted code rate 9.

.. code-block:: yaml

   project-checkers: [unittest]
   file-checkers:
     '*.py': [pylint, pep8]
     'tests/*.py':
       - pylint: {rcfile: tests/pylintrc}

This shows how to set other pylintrc for tests modules

How to set jshint rc file:

.. code-block:: yaml

   file-checkers:
     '*.js': [jshint]
   config:
     jshint: {'command-options': '--config .jshintrc'}


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

#. Install `code-checker` `Installation`_
#. Change current working directory to git repository `cd /path/to/repository`
#. Execute `setup-githooks`. This command creates pre-commit hook which run checkers defined in `precommit-checkers.yml`

.. note::

   Make sure that every requirement of checkers (pylint, pep8, jshint etc.) are installed in your system or active virtual environment.
   You should install them manually.
