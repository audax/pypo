"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from haystack.query import SearchQuerySet
from .models import Item
from readme.scrapers import parse

EXAMPLE_COM = 'http://www.example.com/'


class BasicTests(TestCase):
    fixtures = ['users.json']
    
    def test_item_user_relation(self):
        user = User.objects.get(pk=1)
        item = Item()
        item.url = 'http://www.example.com'
        item.title = 'Title'
        item.owner = user
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

class SearchIntegrationTest(TestCase):
    fixtures = ['users.json']

    def test_item_is_insertet_into_search_index(self):
        Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=User.objects.get(username='dev'),
                            readable_article='test')
        self.assertEqual(1, len(SearchQuerySet().all()), "Search index is empty")



class ScraperText(TestCase):
    fixtures = ['users.json']

    def test_invalid_html(self):
        item = Item.objects.create(url='http://some_invalid_localhost', domain='nothing', owner=User.objects.get(pk=1))
        self.assertEqual((item.url, ''), parse(item, content_type='text/html', text=None))


class ExistingUserIntegrationTest(TestCase):
    fixtures = ['users.json']

    def login(self):
        c = Client()
        assert c.login(username='dev', password='dev')
        return c

    def test_add_item(self):
        c = self.login()
        response = c.post('/add/', {'url': 'http://www.example.com'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, EXAMPLE_COM)

    def test_search_item(self):
        c = self.login()
        Item.objects.create(url=EXAMPLE_COM, title='Example test',
                            owner=User.objects.get(username='dev'),
                             readable_article='test')
        response = c.get('/search/', {'q': 'Example test'}, follow=True)
        self.assertContains(response, 'Results')
        self.assertEqual(1, len(response.context['page'].object_list),
                          'Could not find the test item')



