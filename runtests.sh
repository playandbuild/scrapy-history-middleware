#!/bin/bash

# Test dacrawl using nose.
#    --with-doctest              => located and run doctests
#    --with-cov                  => calculate test coverage
#    --cov-report=html           => generate html report for test coverage
#    --cover-erase               => remove old coverage statistics
#    --cov-config                => use coverage config file

# This script will pass any arguments to the end of the nosetests
# invocation. For example:
#    (venv)$ ./runtests.sh --pdb-failure # will drop into pdb on failure

nosetests \
    --with-doctest \
    --with-cov --cov-report=html --cov-config .coveragerc --cover-erase \
    $@
