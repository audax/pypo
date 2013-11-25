#!/bin/bash
wget https://raw.github.com/jquery/qunit/master/addons/phantomjs/runner.js
python manage.py runserver &
SERVER=$!
sleep 3
phantomjs runner.js http://localhost:8000/static/tests/setup.html
SUCCESS=$?
kill $SERVER
rm runner.js
if python manage.py test; then
    exit $SUCCESS
fi
exit 1
