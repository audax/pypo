#!/bin/bash
if [ "$1" == "js" ]; then
    TESTS=( setup offcanvas)
    wget https://github.com/jonkemp/qunit-phantomjs-runner/raw/master/runner.js
    python manage.py runserver &
    sleep 3
    SERVER=$!
    success=0
    for test in "${TESTS[@]}"; do
        phantomjs runner.js http://localhost:8000/static/tests/$test.html || success=$?
    done;
    kill $SERVER
    rm runner.js
    exit $success
else
    py.test --cov-config .coveragerc --cov readme
fi
