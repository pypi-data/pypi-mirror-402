Development environment
=======================

Installing dependencies
-----------------------

You need to install few dependencies before start coding::

 $ sudo dnf install python-devel podman

Then install all the python dependencies for testing::

 $ pip install -r ./static-checks/requirements-dev.txt
 $ pip install avocado-framework

If you intend to build the documentation locally, please also run::

 $ pip install -r requirements-doc.txt

Installing in develop mode
--------------------------

If you're hacking on Avocado and want to use the same, possibly
modified, source for running your tests and experiments, you may do so with one
additional step::

  $ pip install -e .

It will install the Autils in "editable" mode, which means that you
can modify the source code and the changes will be reflected immediately.

Self-tests
----------

To ensure that the utilities are working properly on all supported platforms
we run the tests in multiple containers with predefined environment using podman. 
To know which platforms are supported for each utility see the yaml files in ./metadata directory.
The tests can be run using the following command::

  $ ./tests/test_module.py

This can can be resources consuming since it will create multiple containers for each utility.
To run the tests for a specific utility you can use the following command::

  $ ./tests/test_module.py metadata/$utility/$utility.yaml

GPG Signatures
--------------

This is an optional step for most contributors, but if you're
interested in ensuring that your contribution is linked to yourself,
this is the best way to do so.

To get a GPG signature, you can find many howtos on the internet, but
it generally works like this::

    $ gpg --gen-key  # defaults are usually fine (using expiration is recommended)
    $ gpg --send-keys $YOUR_KEY    # to propagate the key to outer world

Then, you should enable it in git::

    $ git config --global user.signingkey $YOUR_KEY

Optionally, you can link the key with your GH account:

1. Login to github
2. Go to settings->SSH and GPG keys
3. Add New GPG key
4. run ``$(gpg -a --export $YOUR_EMAIL)`` in shell to see your key
5. paste the key there
