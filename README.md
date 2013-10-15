About Pypo
==========

Pypo is a self hosted bookmarking service like [Pocket](http://www.getpocket.com).
This is a very early alpha. There will be an android application, bookmarklets and
possibly a firefox extension to add, search and view the bookmarks.

It's main components are built with:

 * Python
 * Postgresql
 * Django
 * readability-lxml
 * Whoosh
 * django-haystack
 * django-taggit
 * tld
 * South
 * requests

Features
--------
 * Adding links to the users own link list
 * Fetch summary and title from those links
 * Add tags
 * Search by title, url and tags

Installation
------------

 1. Create a virtualenv and

     pip install -r requirements.txt

 2. Setup a postgresql db
 3. You can overwrite the default settings by creating a settings_local.py next to pypo/settings.py .
    Do not directly edit the settings.py.
 4. Setup the database

    ./manage.py syncdb
    ./manage.py migrate

 5. Add a superuser

    ./manage.py createsuperuser

 6. Host the application, see [Deploying Django with WSGI](https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/)
 7. Create normal users with the admin interface /admin
 8. That should do it.

License
-------
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
