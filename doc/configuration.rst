Configuration
=============

You can overwrite all default settings either directly in pypo/settings.py or you create the file pypo/settings_local.py
which is imported in the pypo/settings.py and therefore can overwrite all settings.

``SECRET_KEY``
==============
Like in all django application, you have to set a unique secret key. `Django SECRET_KEY documentation`_

``DEBUG, TEMPLATE_DEBUG, CRISPY_FAIL_SILENTLY``
===========================================
To enable or disable debugging (crispy is a form component)

``ALLOWED_HOSTS``
==================
A list of hostnames. `Django ALLOWED_HOSTS documentation`_

``ADMINS``
==========
A list of tuples ("name", "email") of admins

``STATIC_ROOT``
===============
Absolute path where your static file are collected to when you call ``./manage.py collectstatic``

``STATIC_URL``
==============
Url where those files are available

``DATABASES``
=============
You database config. Pypo is tested with PostgreSQL, but any django supported DB should be
fine. `Django DATABASES documentation`_

``HAYSTACK_CONNECTIONS``
=======================
If you want to use something else than Whoosh (a pure python search index), you can configure
the search backend here. `Django Haystack documentation`_
It is recommended to switch to Elasticsearch for larger datasets:
  HAYSTACK_CONNECTIONS = {
      'default': {
          'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
          'URL': 'http://127.0.0.1:9200/',
          'INDEX_NAME': 'pypo',
      },
  }



.. _Django SECRET_KEY documentation: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY
.. _Django ALLOWED_HOSTS documentation: https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
.. _Django DATABASES documentation: https://docs.djangoproject.com/en/dev/ref/settings/#databases
.. _Django Haystack documentation: http://django-haystack.readthedocs.org/en/latest/settings.html#haystack-connections
