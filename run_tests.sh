#!/bin/bash
if [ "$1" == "js" ]; then
    TESTS=( setup offcanvas)
    wget https://raw.github.com/jquery/qunit/master/addons/phantomjs/runner.js
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
    exec python manage.py test "$1"
fi
