#!/bin/bash

coverage run -p --source=flowr --omit="runtests.py" ./tests.py
if [ "$?" = "0" ]; then
    coverage combine
    echo -e "\n\n================================================"
    echo "Test Coverage"
    coverage report
    echo -e "\n"
fi
