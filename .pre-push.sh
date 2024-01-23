#!/bin/bash

# Run Django tests before pushing
python manage.py test > /dev/null 2>&1

# Check the exit code
if [ $? -ne 0 ]; then
    echo -e "\nTEST FAILED!!!"
    echo -e "Please run \"python manage.py test\" and debug.\n"
    exit 1
fi
