"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from time import sleep
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore

from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pypo import settings

class ExistingUserTest(LiveServerTestCase):

    fixtures = ['users.json']

    def setUp(self):
        self.b = webdriver.Firefox()
        self.b.implicitly_wait(3)
        self.c = Client()

    def tearDown(self):
        self.b.quit()

    def test_login_dev_user(self):
        self.b.get(self.live_server_url)

        # He sees the login form and sends it
        self.assertEquals('Username*', self.b.find_element_by_id('div_id_username').text,
                          'Login form not found')
        input_username = self.b.find_element_by_name('username')
        input_username.send_keys('dev')
        input_pass = self.b.find_element_by_name('password')
        input_pass.send_keys('dev')
        input_pass.send_keys(Keys.ENTER)

        # He can see the navigation bar
        self.assertIsNotNone(self.b.find_element_by_id('id_link_add'), 'Add item link not found')

    def test_can_add_an_item_and_see_it_in_the_list(self):
        self.create_pre_authenticated_session()

        # User opens pypo and has no items in his list
        self.b.get(self.live_server_url)
        self.assertEquals(0, len(self.b.find_elements_by_class_name('item')))

        # He opens the add item page and sees the form
        self.b.get(self.live_server_url+'/add')

        # He submits a link
        input_url = self.b.find_element_by_name('url')
        input_url.send_keys('http://www.example.com')
        input_url.send_keys(Keys.ENTER)

        # The link is now in his list
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEquals(1, len(items), 'Item was not added')
        self.assertEquals(u'http://www.example.com/', items[0].get_attribute('href'))

        # The domain is in the link text
        self.assertIn(u'[example.com]', items[0].text)

    def create_pre_authenticated_session(self):
        user = User.objects.create(username='uther')
        session = SessionStore()
        session[SESSION_KEY] = user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session.save()
        ## to set a cookie we need to first visit the domain.
        ## 404 pages load the quickest!
        self.b.get(self.live_server_url + "/404_no_such_url/")
        self.b.add_cookie(dict(
            name=settings.SESSION_COOKIE_NAME,
            value=session.session_key,
            path='/',
        ))

