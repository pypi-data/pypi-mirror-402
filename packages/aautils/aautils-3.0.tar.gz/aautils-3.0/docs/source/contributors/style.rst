.. _code_style_guide:

Style guides
============

Commit style guide
------------------

Write a good commit message, pointing motivation, issues that you're
addressing. Usually you should try to explain 3 points in the commit message:
motivation, approach and effects::

    header          <- Limited to 72 characters. No period.
                    <- Blank line
    message         <- Any number of lines, limited to 72 characters per line.
                    <- Blank line
    Reference:      <- External references, one per line (issue, trello, ...)
    Signed-off-by:  <- Signature and acknowledgment of licensing terms when
                       contributing to the project (created by git commit -s)

Signing commits
~~~~~~~~~~~~~~~

If you've set a GPG signature, it's a good idea to put it in use when
committing your changes.  To sign your commits, add the ``-S`` command
line option, such as in::

    $ git commit -S

And if you are merging branches::

    $ git merge -S

.. warning::
   If you use the merge button on GitHub, the signature will be
   performed with GitHub's own private key.  Please check whether you
   find that acceptable or not.

Code style guide
----------------

Avocado uses the Black code style checker, and thus, you should follow
its very opinionated style.  In reality, it's recommended to use your
editor or IDE features to make sure the style is applied
automatically.  Please refer to the `black documentation
<https://black.readthedocs.io/en/stable/index.html>`__ for more
information.

Docstring style guide
---------------------

Docstrings are enforced by the by pylint, and should follow
the `sphinx style <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html#the-sphinx-docstring-format>`__ .
The docstrings should be placed at the beginning of the module, class or
function, and should be enclosed by triple double quotes.  The docstring
should contain a summary line, followed by a blank line and a more detailed
description. The docstring should also contain a params, raises, returns and
examples section, if applicable.

The docstring will be used to generate the documentation, so it's important
to keep it up to date and accurate.

Static checkers
---------------
The AAutils project uses static analysis tools to ensure the code is
consistent and free of errors. You can run the static checks by running::

    $ git submodule update --remote
    $ pip install -r static-checks/requirements.txt
    $ ./static-checks/run-static-checks
