How can I contribute?
=====================

.. note:: Except where otherwise indicated in a given source file, all original
  contributions to AAutils are licensed under the GNU General Public
  License version 2 `(GPLv2) <https://www.gnu.org/licenses/gpl-2.0.html>`_
  or any later version.

  By contributing you agree with: a) our code of conduct; b) that these
  contributions are your own (or approved by your employer), and c) you grant a
  full, complete, irrevocable copyright license to all users and developers of
  the AAutils project, present and future, pursuant to the license of the
  project.


Report a bug
------------

If AAutils crashes on you, or if one of the AAutils "tests" fail,
congratulations, you may have just found a bug. And If you have
precise steps to reproduce, awesome! You're on your way to reporting a
useful bug report.

Don't be afraid to report bugs, even if you're not sure if they're valid. The
most that can happen is that we find out together that this is a feature
instead!

AAutils is using GitHub's issue tracking system for collecting and discussing
issues. If you have a possible candidate, do not hesitate, share with us by
`creating a new issue <https://github.com/avocado-framework/aautils/issues/new>`_.

Contribute with code
--------------------

AAutils uses GitHub and its pull request development model. You can find
a primer on how to use GitHub pull requests `here
<https://help.github.com/articles/using-pull-requests>`_.

Every Pull Request you send will be automatically tested by the
`CI system <https://github.com/avocado-framework/aautils/actions>`_ and review
will take place in the Pull Request as well.

Git workflow
~~~~~~~~~~~~

- `Fork the repository <https://github.com/avocado-framework/aautils/fork>`_
  in GitHub.

- Clone from your fork::

    $ git clone --recurse-submodules git@github.com:<username>/AAutils.git

.. note:: The ``--recurse-submodules`` option is used to checkout the
          contents from the `avocado-static-checks
          <https://github.com/avocado-framework/avocado-static-checks>`_
          repository, which is not needed for general AAutils installations,
          but which is very important for development purposes.

- Enter the directory::

    $ cd AAutils

- Create a ``remote``, pointing to the upstream::

    $ git remote add upstream git@github.com:avocado-framework/aautils.git

- Configure your name and e-mail in git::

    $ git config --global user.name "Your Name"
    $ git config --global user.email email@foo.bar

- Golden tip: never work on local branch main. Instead, create a new
  local branch and checkout to it::

    $ git checkout -b my_new_local_branch

- Code and then commit your changes::

    $ git add new-file.py
    $ git commit -s
    # or "git commit -as" to commit all changes

.. seealso:: Please, read our :ref:`code_style_guide`.

- Make sure your code is working (install your version of AAutils, test
  your change to make sure you didn't introduce any regressions).

- Rebase your local branch on top of upstream main::

    $ git fetch
    $ git rebase upstream/main
    (resolve merge conflicts, if any)

- Push your commit(s) to your fork::

    $ git push origin my_new_local_branch

- `Create the Pull Request
  <https://github.com/avocado-framework/aautils/compare>`_ on
  GitHub. Add the relevant information to the Pull Request
  description.

- Ask maintainers of utility which you are changing for a 
  `review <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/requesting-a-pull-request-review>`_.
  You will find the list of maintainers in the `metadata.yaml <https://github.com/avocado-framework/aautils/tree/main/metadata>_` file.

- Check if your Pull Request passes the CI system. Your Pull Request will
  probably be ignored until it's all green.

Now you're waiting for feedback on GitHub Pull Request page. Once you get some,
join the discussion, answer the questions, make clear if you're going to change
the code based on some review and, if not, why. Feel free to disagree with the
reviewer, they probably have different use cases and opinions, which is
expected. Try describing yours and suggest other solutions, if necessary.

Then, proceed to make the changes.  This is a typical workflow:

- Code, and amend the commit(s) and/or create new commits. If you have
  more than one commit in the PR, you will probably need to rebase
  interactively to amend the right commits. ``git cola`` or ``git citool``
  can be handy here.

- Rebase your local branch on top of upstream main::

    $ git fetch
    $ git rebase upstream/main
    (resolve merge conflicts, if any)

- Push your changes::

    $ git push --force origin my_new_local_branch

Please communicate to the reviewers what the summary of changes are.
Also, make use of GitHub's features to ease the reviewers' life, such
as marking comments as "resolved".  Reviewers should make use of
GitHub's "compare" feature to more easily verify the changes since the
last iteration.

After your PR gets merged, you can sync the main branch on your local
repository propagate the sync to the main branch in your fork repository on
GitHub::

    $ git checkout main
    $ git pull upstream main
    $ git push

From time to time, you can remove old branches to avoid pollution::

    # To list branches along with time reference:
    $ git for-each-ref --sort='-authordate:iso8601' --format=' %(authordate:iso8601)%09%(refname)' refs/heads
    # To remove branches from your fork repository:
    $ git push origin :my_old_branch

Code Review
~~~~~~~~~~~

Every single Pull Request in AAutils has to be reviewed by at least one maintainer.
All maintainers have permission to merge a Pull
Request, but some conditions have to be fulfilled before merging the code:

- Pull Request has to pass the CI tests.
- One 'Approved' code review should be given.
- No explicit disapproval should be present.

Pull Requests failing in CI will not be merged, and reviews won't be given to
them until all the problems are sorted out. In case of a weird failure, or
false-negative (eg. due to too many commits in a single PR), please reach the
maintainers by @name/email or other means.
