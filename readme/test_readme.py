from django.core.paginator import Page
from haystack.query import SearchQuerySet
from unittest.mock import Mock
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
import requests
from .models import Item
from readme.scrapers import parse
from readme import serializers, download
from rest_framework.exceptions import ParseError
from unittest import mock
from readme.views import Tag
import json

from readme.test_item import add_example_item, add_item_for_new_user

import pytest

EXAMPLE_COM = 'http://www.example.com/'
QUEEN = 'queen with spaces änd umlauts'


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

@pytest.mark.django_db
class TestScraperText:

    def test_invalid_html(self, user):
        item = Item.objects.create(url='http://some_invalid_localhost', title='nothing', owner=user)
        assert (item.url, '') == parse(item, content_type='text/html', text=None)



@pytest.mark.django_db
class TestUnknownUser:

    def test_item_access_restricted_to_owners(self, client):
        item = Item.objects.create(url='http://some_invalid_localhost', title='nothing',
                                   owner=User.objects.create(username='somebody', password='something'))
        response = client.get('/view/{}/'.format(item.id))
        assert 302 == response.status_code, 'User did not get redirected trying to access to a foreign item'

    def test_login_required(self, client):
        item = Item.objects.create(url='http://some_invalid_localhost', title='nothing',
                                   owner=User.objects.create(username='somebody', password='something'))
        urls = ['', '/add/', '/view/{}/'.format(item.id), '/delete/{}/'.format(item.id), '/search/']
        for url in urls:
            response = client.get(url)
            assert 302 == response.status_code, 'url "{}" did not redirect for an anonymus user'.format(url)

@pytest.mark.django_db
class TestExistingUserIntegration:

    def test_add_item(self, user_client, get_mock):
        response = user_client.post('/add/', {'url': EXAMPLE_COM, 'tags': 'example-tag'}, follow=True)
        assert response.status_code == 200
        assert EXAMPLE_COM in response.rendered_content
        assert 'example-tag' in response.rendered_content

    def test_edit_item(self, user_client, user):
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=user)
        response = user_client.post('/update/{}/'.format(item.id), {'tags': 'some-tags are-posted'}, follow=True)
        assert response.status_code == 200
        assert 'some-tags' in response.rendered_content
        assert 'are-posted' in response.rendered_content
        item_refreshed = Item.objects.get(pk=item.id)
        assert set(item_refreshed.tags.names()) == {'some-tags', 'are-posted'}

    def test_tags_are_shown_in_the_list(self, user_client, user):
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=user)
        item.tags.add('foo-tag', 'bar-tag', 'bar tag')
        item.save()
        response = user_client.get('/')
        assert 'foo-tag' in response.rendered_content
        assert 'bar-tag' in response.rendered_content
        assert set(response.context['tags']) == {
            Tag('foo-tag', 1, []),
            Tag('bar tag', 1, []),
            Tag('bar-tag', 1, [])}

    def test_tag_view_has_abritary_many_arguments(self):
        match = resolve('/tags/queen/fish')
        assert match.kwargs['tags'] == 'queen/fish'
        match = resolve('/tags/')
        assert match.kwargs['tags'] == ''

    def test_tag_view_filters_items(self, user_client, user, tagged_items):

        tags = [QUEEN, 'fish']
        queryset = Item.objects.filter(owner_id=user.id).tagged(*tags)
        matching_item = queryset.get()
        tag_names = ','.join(tags)
        response = user_client.get(reverse('tags', kwargs={'tags': tag_names}))
        context = response.context
        assert {(tag.name, tag.count) for tag in context['tags']} == {(QUEEN, 1), ('fish', 1)}
        assert set(context['current_item_list']), {matching_item}

    def test_tag_view_redirects_without_arguments(self, user_client):
        response = user_client.get(reverse('tags', kwargs={'tags': ''}))
        assert response.status_code == 302


    def test_tags_can_have_the_same_slug(self, user):
        first = add_example_item(user, ['some-tag'])
        second = add_example_item(user, ['some tag'])
        assert first == Item.objects.tagged('some-tag').get()
        assert second == Item.objects.tagged('some tag').get()

@pytest.mark.django_db
class TestSearchIntegration:

    def test_facets_are_included_in_the_index_view(self, user_client, tagged_items, test_index):
        # another item with the same tag by another user
        add_item_for_new_user([QUEEN])
        response = user_client.get('/')
        tags = {(tag.name, tag.count) for tag in response.context['tags']}
        # only his own tags are counted
        assert {(QUEEN, 3), ('fish', 2), ('pypo', 1), ('boxing', 1), ('bartender', 1)}, tags

    def test_index_view_is_paginated(self, user, user_client, tagged_items):
        response = user_client.get('/')
        assert isinstance(response.context['current_item_list'], Page)

        p = response.context['current_item_list']
        # start at page 1
        assert p.number == 1

        response = user_client.get('/?page=100')
        p = response.context['current_item_list']
        # overflowing means that we get the last page
        assert p.number == p.paginator.num_pages

    def test_tags_are_saved_as_a_list(self, user, test_index):
        item = Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=user, readable_article='test')
        tags = ['foo', 'bar']
        item.tags.add(*tags)
        item.save()
        sqs = SearchQuerySet().filter(owner_id=user.id)
        assert 1 == len(sqs)
        result = sqs[0]
        assert set(tags) == set(result.tags)

    def test_search_item_by_title(self, user_client, user, test_index):
        Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=user, readable_article='test')
        response = user_client.get('/search/', {'q': 'Example test'})
        assert 'Results' in response.content.decode('utf8')
        assert 1 == len(response.context['page'].object_list), 'Could not find the test item'

    def test_search_item_by_tag(self, user_client, user, test_index):
        item = Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=user, readable_article='test')
        item.tags.add('example-tag')
        item.save()
        response = user_client.get('/search/', {'q': 'example-tag'})
        assert 'Results' in response.content.decode('utf8')
        assert 1 == len(response.context['page'].object_list), 'Could not find the test item'

    def test_user_can_only_search_own_items(self, user_client, user, other_user, test_index):
        item = Item.objects.create(url=EXAMPLE_COM, title='Example test',
                                   owner=other_user, readable_article='test')
        item.tags.add('example-tag')
        item.save()
        response = user_client.get('/search/', {'q': 'example-tag'})
        assert 'Results' in response.content.decode('utf8')
        assert 0 == len(response.context['page'].object_list), 'Item from another user found in search'

    def test_tags_are_added_to_form(self, test_index, user_client, tagged_items):
        response = user_client.get('/add/')
        tags = [QUEEN, 'fish', 'bartender', 'pypo']
        for tag in tags:
            json_tag = json.dumps(tag)
            assert json_tag in response.context['tags']
            assert json_tag in response.content.decode('utf-8')

    def test_can_query_for_tags(self, user, test_index, tagged_items):
        tags = [QUEEN, 'fish']
        tagged_items = Item.objects.filter(owner=user).tagged(*tags)
        # tags__in with multiple calls and single values each _should_ be the same
        # as tags=[], but it isn't. Probably a bug in Haystack or Whoosh
        sqs = SearchQuerySet().filter(owner_id=user.id)
        for tag in tags:
            sqs = sqs.filter(tags__in=[tag])
        searched = {result.object for result in sqs}
        assert set(tagged_items) == searched


class TestDownload:

    def _mock_content(self, get_mock, content, content_type="", content_length=1, encoding=None):
        return_mock = Mock(headers={'content-type': content_type,
                                    'content-length': content_length},
                           encoding=encoding)
        return_mock.iter_content.return_value = iter([content])
        get_mock.return_value = return_mock

    def test_uses_request_to_start_the_download(self, get_mock):
        get_mock.side_effect = requests.RequestException
        with pytest.raises(download.DownloadException):
            download.download(EXAMPLE_COM)
        get_mock.assert_called_with(EXAMPLE_COM, stream=True, verify=False)

    def test_aborts_large_downloads(self, get_mock):
        max_length = 1000
        return_mock = Mock(headers={'content-length': max_length+1})
        get_mock.return_value = return_mock
        with pytest.raises(download.DownloadException) as cm:
            download.download(EXAMPLE_COM, max_length)
        assert 'content-length' in cm.value.message

    def test_aborts_with_invalid_headers(self, get_mock):
        return_mock = Mock(headers={'content-length': "invalid"})
        get_mock.return_value = return_mock
        with pytest.raises(download.DownloadException) as cm:
            download.download(EXAMPLE_COM)
        assert 'content-length' in cm.value.message
        assert 'convert' in cm.value.message
        assert isinstance(cm.value.parent, ValueError)

    def test_only_downloads_up_to_a_maximum_length(self, get_mock):
        content = Mock()
        max_length = 1
        self._mock_content(get_mock, content=content, content_length=max_length)
        ret = download.download(EXAMPLE_COM, max_content_length=max_length)
        get_mock.return_value.iter_content.assert_called_with(max_length)
        assert ret.content == content

    def test_decodes_text_content(self, get_mock):
        content, encoding = Mock(), Mock()
        content.decode.return_value = 'text'
        self._mock_content(get_mock, content=content, content_type='text/html', encoding=encoding)
        ret = download.download(EXAMPLE_COM)
        content.decode.assert_called_with(encoding, errors='ignore')
        assert 'text' == ret.text

    def test_ignores_invalid_decode(self, get_mock):
        content, encoding = "üöä".encode('utf-8'), 'ascii'
        self._mock_content(get_mock, content=content, content_type='text/html', encoding=encoding)
        ret = download.download(EXAMPLE_COM)
        # expect the empty fallback text because the decode had only errors
        assert '' == ret.text

    def test_only_decodes_text_content(self, get_mock):
        content = Mock()
        self._mock_content(get_mock, content=content, content_type="something/else")
        ret = download.download(EXAMPLE_COM)
        # expect the empty fallback text because the decode failed
        assert None == ret.text


@pytest.mark.django_db
class TestAPI:

    def test_can_list_all_items(self, api_client, api_user):
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=api_user)
        item2 = Item.objects.create(url='something.local', title='nothing', owner=api_user)
        response = api_client.get('/api/items/')
        response.data[0].pop('id')
        response.data[1].pop('id')
        assert response.data == [
            {'url': 'something.local', 'title': 'nothing',
             'created': item2.created, 'readable_article': None, 'tags': []},
            {'url': 'http://www.example.com/', 'title': 'nothing',
             'created': item.created, 'readable_article': None, 'tags': []},
        ]

    def test_can_update_item(self, api_client, api_user):
        item = Item.objects.create(url=EXAMPLE_COM, title='nothing', owner=api_user)
        response = api_client.put('/api/items/{}/'.format(item.id),
                                  {'url': item.url, 'tags': ['test-tag', 'second-tag']},
                                  format='json')
        assert response.data['id'] == item.id
        assert set(response.data['tags']) == {'test-tag', 'second-tag'}

    def test_items_are_searchable(self, api_client, api_user):
        response = api_client.post('/api/items/', {'url': EXAMPLE_COM, 'tags': ['test-tag', 'second-tag']},
                                    format='json')
        assert 'id' in response.data
        sqs = SearchQuerySet().filter(owner_id=api_user.id).auto_query('second-tag')
        assert sqs.count() == 1, 'New item is not in the searchable by tag'
