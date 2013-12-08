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
    exec coverage run --source='readme,pypo' --omit='pypo/wsgi.py,readme/migrations/*,readme/tests.py' manage.py test readme functional_tests
fi
