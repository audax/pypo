About Pypo
==========

|Build Status|

Pypo is a self hosted bookmarking service like `Pocket`_. This is a very
early alpha. There will be an android application, bookmarklets and
possibly a firefox extension to add, search and view the bookmarks.

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

Documentation
-------------
Full documentation can be found at `readthedocs`_

Features
--------

-  Adding links to the users own link list
-  Fetch summary and title from those links
-  Add tags
-  Search by title, url and tags

Installation
------------

1. Create a virtualenv and

   pip install -r requirements.txt

2. Setup a postgresql db
3. You can overwrite the default settings by creating a
   settings\_local.py next to pypo/settings.py . Do not directly edit
   the settings.py.
4. Setup the database

   ./manage.py syncdb
   ./manage.py migrate

5. Add a superuser

   ./manage.py createsuperuser

6. Host the application, see `Deploying Django with WSGI`_
7. Create normal users with the admin interface /admin
8. That should do it.

Deploying
---------
There is a fab file you can custome to you liking. It creates a virtualenv,
sets up the directory structure and checks your current local commit out
on the target machine.

License
-------

This project is licensed under the terms of the Apache License version
2. See COPYING.txt for details.

.. _Pocket: http://www.getpocket.com
.. _Deploying Django with WSGI: https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
.. _readthedocs: http://pypo.readthedocs.org/
.. |Build Status| image:: https://drone.io/bitbucket.org/audax/pypo/status.png
   :target: https://drone.io/bitbucket.org/audax/pypo/latest
