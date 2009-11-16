#!/bin/bash

find . -name "*_test.py" -exec echo "Running test: '{}'" \; -exec python2.5 '{}' \; -exec echo \;

# Cleanup .pyc files
find . -name "*.pyc" -execdir rm '{}' \;
