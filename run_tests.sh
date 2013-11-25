#!/bin/bash
if [ "$1" == "js" ]; then
    wget https://raw.github.com/jquery/qunit/master/addons/phantomjs/runner.js
    python manage.py runserver &
    sleep 3
    SERVER=$!
    phantomjs runner.js http://localhost:8000/static/tests/setup.html
    SUCCESS=$?
    kill $SERVER
    rm runner.js
    exit $SUCCESS
else
    exec python manage.py test "$1"
fi
