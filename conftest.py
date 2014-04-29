import os
import sys
import pytest

import haystack
from rest_framework.test import APIClient

from django.core.management import call_command
from unittest.mock import patch, Mock
from readme.models import User, Item

from django.conf import settings

def pytest_configure():
    # workaround to avoid django pipeline issue
    # refers to
    settings.STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'

QUEEN = 'queen with spaces änd umlauts'
EXAMPLE_COM = 'http://www.example.com/'


@pytest.fixture
def user(db):
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@example.com',
                                        'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()
    return user

@pytest.fixture
def other_user(db):
    try:
        user = User.objects.get(username='other_user')
    except User.DoesNotExist:
        user = User.objects.create_user('other_user', 'other_user@example.com',
                                        'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()
    return user

@pytest.fixture
def api_user(db):
    try:
        user = User.objects.get(username='dev')
    except User.DoesNotExist:
        user = User.objects.create_user('dev', 'dev@example.com',
                                        'dev')
        user.is_staff = True
        user.is_superuser = True
        user.save()
    return user

@pytest.fixture
def user_client(client, user):
    client.login(username='admin', password='password')
    return client

@pytest.fixture
def api_client(api_user):
    client = APIClient()
    client.login(username='dev', password='dev')
    return client

def add_example_item(user, tags=None):
    item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=user)
    if tags is not None:
        item.tags.add(*tags)
        item.save()
    return item

@pytest.yield_fixture(scope='module')
def tagged_items(db, user):
    items = [
        add_example_item(user, ('fish', 'boxing')),
        add_example_item(user, ('fish', QUEEN)),
        add_example_item(user, (QUEEN, 'bartender')),
        add_example_item(user, (QUEEN, 'pypo')),
        add_example_item(user, tuple())]
    yield items
    for item in items:
        item.delete()

@pytest.fixture
def clear_index():
    call_command('clear_index', interactive=False, verbosity=0)

@pytest.fixture
def get_mock(request, clear_index):
    patcher = patch('requests.get')
    get_mock = patcher.start()
    return_mock = Mock(headers={'content-type': 'text/html',
                                'content-length': 500},
                       encoding='utf-8')
    return_mock.iter_content.return_value = iter([b"example.com"])
    get_mock.return_value = return_mock

    def fin():
        patcher.stop()
    request.addfinalizer(fin)
    return get_mock


TEST_INDEX = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index_test'),
        },
    }

@pytest.fixture
def test_index(settings):
    settings.HAYSTACK_CONNECTIONS = TEST_INDEX
    call_command('clear_index', interactive=False, verbosity=0)
    haystack.connections.reload('default')

