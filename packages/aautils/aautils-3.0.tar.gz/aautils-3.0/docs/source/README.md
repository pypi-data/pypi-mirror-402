# AAutils

Utility Libraries to power your tests (or general applications)

AAutils, collection of well tested python utilities that will
keep test writers efforts in the features to be tested, and away
from debugging and troubleshooting those libraries.

The primary goal of AAutils is to be a place for modules
that ease the interaction with system level features and interfaces. Which
is commonly needed in test automation.

This list of available utilities and supported platforms can be visible in
https://avocado-framework.github.io/aautils.html.

## Installation

### Installation from PyPi

AAutils is written in Python, so a standard Python installation is possible
and often preferable. The simplest installation method is through pip.
On most POSIX systems with Python 3.8 (or later) and pip available, installation
can be performed with a single command:

$ pip3 install --user aautils

### Installation from source

First make sure you have a basic set of packages installed. The following
applies to Fedora based distributions, please adapt to your platform::

    $ sudo dnf install git python3-pip

Then to install AAutils from the git repository run::

    $ git clone https://github.com/avocado-framework/aautils.git
    $ cd aautils
    $ pip install . --user

### AI-Generated code policy

The AAutils project allows the use of AI-generated code, but it has to follow
the guidelines and requirements outlined in the Policy for AI-Generated Code
which can be found at:

https://avocado-framework.readthedocs.io/en/latest/guides/contributor/chapters/ai_policy.html
