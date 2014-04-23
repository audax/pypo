#!/bin/bash
if [ "$1" == "js" ]; then
    TESTS=( setup )
    python manage.py runserver &
    sleep 3
    SERVER=$!
    success=0
    for test in "${TESTS[@]}"; do
        phantomjs bower_components/qunit-phantomjs-runner/runner.js http://localhost:8000/test/$test || success=$?
    done;
    kill $SERVER
    exit $success
else
    exec py.test --cov-config .coveragerc --cov readme
fi
