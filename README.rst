About Pypo
==========

|Build Status| |Coverage Status|


Pypo is a self hosted bookmarking service like `Pocket`_.
There also is a rudimentary android application and firefox
extension to add and view the bookmarks.

It's main components are built with:

-  Python 3
-  Postgresql
-  Django
-  readability-lxml
-  Whoosh
-  django-haystack
-  django-taggit
-  tld
-  South
-  requests
-  djangorestframework
-  py.test

Documentation
-------------
Full documentation can be found at `readthedocs`_

Features
--------

-  Adding links and fetch their summaries and titles
-  Links can have multiple tags
-  Search by title, url and tags
-  Filter by tags

Installation
------------

1. Create a virtualenv and

   pip install -r requirements.txt
   pip install -e .

2. Setup a postgresql db
3. You can overwrite the default settings by creating a
   settings\_local.py next to pypo/settings.py . Do not directly edit
   the settings.py.
4. Install js modules with bower

   npm install -g bower
   bower install

5. Install yuglify for js and css minifiy

    npm install -g yuglify

6. Setup the database

   ./manage.py syncdb
   ./manage.py migrate

7. Add a superuser

   ./manage.py createsuperuser

8. Host the application, see `Deploying Django with WSGI`_
9. Create normal users with the admin interface /admin

Deploying
---------
There is a fab file you can customize to you liking. It creates a virtualenv,
sets up the directory structure and checks your current local commit out
on the target machine.

License
-------

This project is licensed under the terms of the Apache License version
2. See COPYING.txt for details.

.. _Pocket: http://www.getpocket.com
.. _Deploying Django with WSGI: https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
.. _readthedocs: http://pypo.readthedocs.org/
.. |Build Status| image:: https://travis-ci.org/audax/pypo.png?branch=master
    :target: https://travis-ci.org/audax/pypo
.. |Coverage Status| image:: https://coveralls.io/repos/audax/pypo/badge.png?branch=master
    :target: https://coveralls.io/r/audax/pypo?branch=master
