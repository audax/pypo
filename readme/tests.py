from functools import partial
from unittest.mock import patch, Mock
from django.core.management import call_command
import haystack
from haystack.query import SearchQuerySet
import os
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.core.urlresolvers import reverse, resolve
import requests
from rest_framework.test import APIClient
from .models import Item
from readme.scrapers import parse
from readme import serializers, download
from rest_framework.exceptions import ParseError
from unittest import mock
from readme.views import Tag
import json

EXAMPLE_COM = 'http://www.example.com/'
QUEEN = 'queen with spaces änd umlauts'

TEST_INDEX = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index_test'),
        },
    }

def add_example_item(user, tags=None):
    item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=user)
    if tags is not None:
        item.tags.add(*tags)
        item.save()
    return item

def add_tagged_items(user):
    add_example_item(user, ('fish', 'boxing'))
    add_example_item(user, ('fish', QUEEN))
    add_example_item(user, (QUEEN, 'bartender'))
    add_example_item(user, (QUEEN, 'pypo'))
    add_example_item(user, tuple())


def add_item_for_new_user(tags):
    another_user = User.objects.create(username='someone')
    another_item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=another_user)
    another_item.tags.add(*tags)
    another_item.save()


def add_for_user(user):
    return partial(add_example_item, user)


class TestBase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.user = User.objects.get(pk=1)

class BasicTests(TestBase):

    def test_item_user_relation(self):
        item = Item()
        item.url = 'http://www.example.com'
        item.title = 'Title'
        item.owner = self.user
        item.save()
        self.assertTrue(item.owner)

    def test_summary(self):
        item = Item()
        item.readable_article = 'lorem_ipsum' * 100
        self.assertEqual(item.summary, item.readable_article[:300])

    def test_unknown_tld(self):
        item = Item()
        item.url = 'foobar'
        self.assertEqual(item.domain, None)


class ItemModelTest(TestBase):

    def _add_simple_example_items(self):
        self.item_fish = self.add([QUEEN, 'fish', 'cookie'])
        self.item_box = self.add([QUEEN, 'box'])
        self.filter = Item.objects.filter(owner_id=1)

    def setUp(self):
        super(ItemModelTest, self).setUp()
        self.add = add_for_user(self.user)

    def test_find_items_by_tag(self):
        self._add_simple_example_items()
        self.assertCountEqual(
            [self.item_fish, self.item_box],
            Item.objects.filter(owner_id=1).tagged(QUEEN))

    def test_find_items_by_multiple_tags(self):
        self._add_simple_example_items()
        self.assertEqual(self.item_fish,
                         self.filter.tagged(QUEEN, 'fish').get())
        self.assertEqual(self.item_box,
                         self.filter.tagged(QUEEN, 'box').get())

    def test_chain_tag_filters(self):
        self._add_simple_example_items()
        self.assertEqual(self.item_fish,
                         self.filter.filter(owner_id=1).tagged(QUEEN).tagged('fish').get())
        self.assertEqual(self.item_box,
                         Item.objects.filter(owner_id=1).tagged(QUEEN).tagged('box').get())

    def test_filtering_out(self):
        add_tagged_items(self.user)

        tags = [QUEEN, 'fish']
        queryset = Item.objects.tagged(*tags)
        self.assertEqual(len(queryset), 1, "Exactly one item with these tags should be found, but found: {}".format(
            '/ '.join("Item with tags {}".format(item.tags.names()) for item in queryset)))





class SerializerTest(TestCase):

    tags = "foo bar baz".split()

    def test_taglist_from_native_accepts_list(self):
        serializer = serializers.TagListSerializer()
        self.assertEqual(self.tags, serializer.from_native(self.tags))

    def test_taglist_from_native_fails_for_non_lists(self):
        serializer = serializers.TagListSerializer()
        with self.assertRaises(ParseError):
            serializer.from_native({'not': 'a list'})

    def test_taglist_to_native_accepts_tag_manager(self):
        mock_tag_manager = mock.Mock(all=mock.Mock())
        mock_tags = []
        for tag_name in self.tags:
            tag = mock.Mock()
            tag.name = tag_name
            mock_tags.append(tag)
        mock_tag_manager.all.return_value = mock_tags
        serializer = serializers.TagListSerializer()
        result = serializer.to_native(mock_tag_manager)
        for tag in self.tags:
            self.assertIn(tag, result)
        mock_tag_manager.all.assert_called()

    def test_taglist_to_native_accepts_lists(self):
        serializer = serializers.TagListSerializer()
        tags = "foo bar baz".split()
        self.assertEqual(tags, serializer.to_native(tags))


    def test_taglist_to_native_fails_otherwise(self):
        serializer = serializers.TagListSerializer()
        with self.assertRaises(ParseError):
            serializer.to_native("not a list")

class ScraperText(TestCase):
    fixtures = ['users.json']

    def test_invalid_html(self):
        item = Item.objects.create(url='http://some_invalid_localhost', title='nothing', owner=User.objects.get(pk=1))
        self.assertEqual((item.url, ''), parse(item, content_type='text/html', text=None))


def login():
    c = Client()
    assert c.login(username='dev', password='dev')
    return c


class UnknownUserTest(TestCase):
    fixtures = ['users.json']

    def test_item_access_restricted_to_owners(self):
        c = login()
        item = Item.objects.create(url='http://some_invalid_localhost', title='nothing',
                                   owner=User.objects.create(username='somebody', password='something'))
        response = c.get('/view/{}/'.format(item.id))
        self.assertEqual(302, response.status_code, 'User did not get redirected trying to access to a foreign item')

    def test_login_required(self):
        item = Item.objects.create(url='http://some_invalid_localhost', title='nothing',
                                   owner=User.objects.create(username='somebody', password='something'))
        urls = ['', '/add/', '/view/{}/'.format(item.id), '/delete/{}/'.format(item.id), '/search/']
        c = Client()
        for url in urls:
            response = c.get(url)
            self.assertEqual(302, response.status_code, 'url "{}" did not redirect for an anonymus user'.format(url))


class ExistingUserIntegrationTest(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.patcher = patch('requests.get')
        get_mock = self.patcher.start()
        return_mock = Mock(headers={'content-type': 'text/html',
                                    'content-length': 500},
                           encoding='utf-8')
        return_mock.iter_content.return_value = iter([b"example.com"])
        get_mock.return_value = return_mock
        call_command('clear_index', interactive=False, verbosity=0)

    def tearDown(self):
        self.patcher.stop()

    def test_add_item(self):
        c = login()
        response = c.post('/add/', {'url': EXAMPLE_COM, 'tags': 'example-tag'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, EXAMPLE_COM)
        self.assertContains(response, 'example-tag')

    def test_edit_item(self):
        c = login()
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=User.objects.get(pk=1))
        response = c.post('/update/{}/'.format(item.id), {'tags': 'some-tags are-posted'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'some-tags')
        self.assertContains(response, 'are-posted')
        item_refreshed = Item.objects.get(pk=item.id)
        self.assertCountEqual(item_refreshed.tags.names(), ['some-tags', 'are-posted'])

    def test_tags_are_shown_in_the_list(self):
        c = login()
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=User.objects.get(pk=1))
        item.tags.add('foo-tag', 'bar-tag', 'bar tag')
        item.save()
        response = c.get('/')
        self.assertContains(response, 'foo-tag')
        self.assertContains(response, 'bar-tag')
        self.assertContains(response, 'bar tag')
        self.assertCountEqual(
            response.context['tags'], [
            Tag('foo-tag', 1, []),
            Tag('bar tag', 1, []),
            Tag('bar-tag', 1, [])])

    def test_tag_view_has_abritary_many_arguments(self):
        match = resolve('/tags/queen/fish')
        self.assertEqual(match.kwargs['tags'], 'queen/fish')
        match = resolve('/tags/')
        self.assertEqual(match.kwargs['tags'], '')

    def test_tag_view_filters_items(self):
        c = login()
        add_tagged_items(User.objects.get(pk=1))

        tags = [QUEEN, 'fish']
        queryset = Item.objects.filter(owner_id=1).tagged(*tags)
        matching_item = queryset.get()
        tag_names = ','.join(tags)
        response = c.get(reverse('tags', kwargs={'tags': tag_names}))
        context = response.context
        self.assertCountEqual([(tag.name, tag.count) for tag in context['tags']],
                              [(QUEEN, 1), ('fish', 1)])
        self.assertCountEqual(context['current_item_list'], [matching_item])

    def test_tag_view_redirects_without_arguments(self):
        c = login()
        response = c.get(reverse('tags', kwargs={'tags': ''}))
        self.assertRedirects(response, '/')


    def test_tags_can_have_the_same_slug(self):
        user = User.objects.get(pk=1)
        first = add_example_item(user, ['some-tag'])
        second = add_example_item(user, ['some tag'])
        self.assertEqual(first, Item.objects.tagged('some-tag').get())
        self.assertEqual(second, Item.objects.tagged('some tag').get())

@override_settings(HAYSTACK_CONNECTIONS=TEST_INDEX)
class SearchIntegrationTest(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        haystack.connections.reload('default')
        super(TestCase, self).setUp()
        self.user = User.objects.get(pk=1)
        call_command('clear_index', interactive=False, verbosity=0)

    def tearDown(self):
        pass

    def test_facets_are_included_in_the_index_view(self):
        c = login()
        add_tagged_items(self.user)
        # another item with the same tag by another user
        add_item_for_new_user([QUEEN])
        response = c.get('/')
        tags = [(tag.name, tag.count) for tag in response.context['tags']]
        # only his own tags are counted
        self.assertCountEqual(
            [(QUEEN, 3), ('fish', 2), ('pypo', 1), ('boxing', 1), ('bartender', 1)],
            tags)

    def test_tags_are_saved_as_a_list(self):
        user = User.objects.get(username='dev')
        item = Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=user, readable_article='test')
        tags = ['foo', 'bar']
        item.tags.add(*tags)
        item.save()
        sqs = SearchQuerySet().filter(owner_id=1)
        self.assertEqual(1, len(sqs))
        result = sqs[0]
        self.assertCountEqual(tags, result.tags)

    def test_search_item_by_title(self):
        c = login()
        Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=User.objects.get(username='dev'),
                             readable_article='test')
        response = c.get('/search/', {'q': 'Example test'})
        self.assertContains(response, 'Results')
        self.assertEqual(1, len(response.context['page'].object_list),
                          'Could not find the test item')

    def test_search_item_by_tag(self):
        c = login()
        item = Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=User.objects.get(username='dev'),
                            readable_article='test')
        item.tags.add('example-tag')
        item.save()
        response = c.get('/search/', {'q': 'example-tag'})
        self.assertContains(response, 'Results')
        self.assertEqual(1, len(response.context['page'].object_list),
                         'Could not find the test item')

    def test_user_can_only_search_own_items(self):
        item = Item.objects.create(url=EXAMPLE_COM, title='Example test',
                                   owner=User.objects.get(username='someone_else'),
                                   readable_article='test')
        item.tags.add('example-tag')
        item.save()
        c = login()
        response = c.get('/search/', {'q': 'example-tag'})
        self.assertContains(response, 'Results')
        self.assertEqual(0, len(response.context['page'].object_list),
                         'Item from another user found in search')

    def test_tags_are_added_to_form(self):
        c = login()
        add_tagged_items(self.user)
        response = c.get('/add/')
        tags = [QUEEN, 'fish', 'bartender', 'pypo']
        for tag in tags:
            json_tag = json.dumps(tag)
            self.assertIn(json_tag, response.context['tags'])
            self.assertContains(response, json_tag)

    def test_can_query_for_tags(self):
        add_tagged_items(self.user)
        tags = [QUEEN, 'fish']
        tagged_items = Item.objects.filter(owner=self.user).tagged(*tags)
        # tags__in with multiple calls and single values each _should_ be the same
        # as tags=[], but it isn't. Probably a bug in Haystack or Whoosh
        sqs = SearchQuerySet().filter(owner_id=self.user.id)
        for tag in tags:
            sqs = sqs.filter(tags__in=[tag])
        searched = [result.object for result in sqs]
        self.assertCountEqual(tagged_items, searched)


@patch('requests.get')
class DownloadTest(TestCase):

    def _mock_content(self, get_mock, content, content_type="", content_length=1, encoding=None):
        return_mock = Mock(headers={'content-type': content_type,
                                    'content-length': content_length},
                           encoding=encoding)
        return_mock.iter_content.return_value = iter([content])
        get_mock.return_value = return_mock

    def test_uses_request_to_start_the_download(self, get_mock):
        get_mock.side_effect = requests.RequestException
        with self.assertRaises(download.DownloadException):
            download.download(EXAMPLE_COM)
        get_mock.assert_called_with(EXAMPLE_COM, stream=True, verify=False)

    def test_aborts_large_downloads(self, get_mock):
        max_length = 1000
        return_mock = Mock(headers={'content-length': max_length+1})
        get_mock.return_value = return_mock
        with self.assertRaises(download.DownloadException) as cm:
            download.download(EXAMPLE_COM, max_length)
        self.assertIn('content-length', cm.exception.message)

    def test_aborts_with_invalid_headers(self, get_mock):
        return_mock = Mock(headers={'content-length': "invalid"})
        get_mock.return_value = return_mock
        with self.assertRaises(download.DownloadException) as cm:
            download.download(EXAMPLE_COM)
        self.assertIn('content-length', cm.exception.message)
        self.assertIn('convert', cm.exception.message)
        self.assertIsInstance(cm.exception.parent, ValueError)

    def test_only_downloads_up_to_a_maximum_length(self, get_mock):
        content = Mock()
        max_length = 1
        self._mock_content(get_mock, content=content, content_length=max_length)
        ret = download.download(EXAMPLE_COM, max_content_length=max_length)
        get_mock.return_value.iter_content.assert_called_with(max_length)
        self.assertEqual(ret.content, content)

    def test_decodes_text_content(self, get_mock):
        content, encoding = Mock(), Mock()
        content.decode.return_value = 'text'
        self._mock_content(get_mock, content=content, content_type='text/html', encoding=encoding)
        ret = download.download(EXAMPLE_COM)
        content.decode.assert_called_with(encoding, errors='ignore')
        self.assertEqual('text', ret.text)

    def test_ignores_invalid_decode(self, get_mock):
        content, encoding = "üöä".encode('utf-8'), 'ascii'
        self._mock_content(get_mock, content=content, content_type='text/html', encoding=encoding)
        ret = download.download(EXAMPLE_COM)
        # expect the empty fallback text because the decode had only errors
        self.assertEqual('', ret.text)

    def test_only_decodes_text_content(self, get_mock):
        content = Mock()
        self._mock_content(get_mock, content=content, content_type="something/else")
        ret = download.download(EXAMPLE_COM)
        # expect the empty fallback text because the decode failed
        self.assertEqual(None, ret.text)


@override_settings(HAYSTACK_CONNECTIONS=TEST_INDEX)
class APITest(TestCase):
    fixtures = ['users.json']

    client_class = APIClient

    def setUp(self):
        haystack.connections.reload('default')

    def tearDown(self):
        call_command('clear_index', interactive=False, verbosity=0)

    def api_login(self):
        assert self.client.login(username='dev', password='dev')

    def _fetch_item_details(self, item_id):
        return self.client.get('/api/items/{}'.format(item_id))

    def test_can_list_all_items(self):
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=User.objects.get(pk=1))
        item2 = Item.objects.create(url='something.local', title='nothing', owner=User.objects.get(pk=1))
        self.api_login()
        response = self.client.get('/api/items/')
        self.assertCountEqual(response.data, [
            {'id': 1, 'url': 'http://www.example.com/', 'title': 'nothing',
             'created': item.created, 'readable_article': None, 'tags': []},
            {'id': 2, 'url': 'something.local', 'title': 'nothing',
             'created': item2.created, 'readable_article': None, 'tags': []}
        ])

    def test_can_update_item(self):
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=User.objects.get(pk=1))
        self.api_login()
        response = self.client.put('/api/items/{}/'.format(item.id), {'url': item.url, 'tags': ['test-tag', 'second-tag']},
                               format='json')
        self.assertEqual(response.data['id'], item.id)
        self.assertEqual(response.data['tags'], ['test-tag', 'second-tag'])

    def test_items_are_searchable(self):
        self.api_login()
        response = self.client.post('/api/items/', {'url': EXAMPLE_COM, 'tags': ['test-tag', 'second-tag']},
                                    format='json')
        self.assertTrue('id' in response.data)
        sqs = SearchQuerySet().filter(owner_id=1).auto_query('second-tag')
        self.assertEqual(sqs.count(), 1, 'New item is not in the searchable by tag')
