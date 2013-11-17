#!/bin/sh
wget https://raw.github.com/jquery/qunit/master/addons/phantomjs/runner.js
./manage.py runserver &
SERVER=$!
sleep 5
phantomjs runner.js http://localhost:8000/static/tests/setup.html
SUCCESS=$?
kill $SERVER
rm runner.js
exit $SUCCESS
