"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from .models import Item


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


class FunctionalTests(TestCase):
    fixtures = ['users.json']

    def test_add_item(self):
        c = Client()
        assert c.login(username='dev', password='dev')
        response = c.post('/add/', {'url': 'http://www.example.com'}, follow=True)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        assert 'http://www.example.com/' in content



