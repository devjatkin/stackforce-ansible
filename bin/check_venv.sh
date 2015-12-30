#!/bin/bash

if [ -z $VIRTUAL_ENV ]; then
        # The virtualenv variable is null, so we are not in
        # an active virtual environment.
        echo "Not in a virtual environment"
        exit 1
fi
