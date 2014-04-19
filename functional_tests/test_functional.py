import sys
from unittest.mock import patch, Mock

from django.core.management import call_command
import haystack
import os
from django.utils.http import urlquote
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.test import LiveServerTestCase
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from pypo import settings
from readme.test_item import add_example_item, add_tagged_items, add_item_for_new_user, QUEEN


EXAMPLE_COM = 'http://www.example.com/'

TEST_INDEX = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index_test'),
        },
    }


class PypoLiveServerTestCase(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url = arg.split('=')[1]
                return
        LiveServerTestCase.setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            LiveServerTestCase.tearDownClass()



TEST_INDEX = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index_test'),
        },
    }

@override_settings(HAYSTACK_CONNECTIONS=TEST_INDEX)
class ExistingUserTest(PypoLiveServerTestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.b = webdriver.Firefox()
        #self.b = webdriver.PhantomJS()
        self.b.implicitly_wait(3)
        self.b.set_window_size(1024, 768)
        self.c = self.client
        haystack.connections.reload('default')
        self.patcher = patch('requests.get')
        get_mock = self.patcher.start()
        return_mock = Mock(headers={'content-type': 'text/html',
                                    'content-length': 500},
                           encoding='utf-8')
        return_mock.iter_content.return_value = iter([b"example.com"])
        get_mock.return_value = return_mock
        haystack.connections.reload('default')
        try:
            user = User.objects.get(username='uther')
        except User.DoesNotExist:
            user = User.objects.create(username='uther')
        self.user = user

    def tearDown(self):
        self.b.quit()
        self.patcher.stop()
        call_command('clear_index', interactive=False, verbosity=0)

    def create_pre_authenticated_session(self):
        session = SessionStore()
        session[SESSION_KEY] = self.user.pk
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

    def _add_example_item(self, tags=None):
        return add_example_item(self.user, tags)

    def _add_tagged_items(self):
        add_tagged_items(self.user)

    def _find_tags_from_detail(self):
        tags = self.b.find_elements_by_css_selector('.tag-list .tag')
        return [t.text for t in tags]

    def create_example_item(self, tags='super-tag'):
        self.b.get(self.live_server_url + '/add')
        # He submits a link
        input_url = self.b.find_element_by_name('url')
        input_url.send_keys(EXAMPLE_COM)
        input_tags = self.b.find_element_by_id('id_tags-tokenfield')
        input_tags.click()
        input_tags.send_keys(tags)
        input_tags.send_keys(',')
        self.b.find_element_by_id('submit-id-submit').click()

    def test_autocomplete_tags(self):
        example_address = 'http://foobar.local/'
        self.create_pre_authenticated_session()
        self._add_tagged_items()
        self.b.get(self.live_server_url + '/add')
        input_url = self.b.find_element_by_name('url')
        input_url.send_keys(example_address)
        # He activates the input field for tags
        self.b.find_element_by_css_selector('#id_tags-tokenfield').click()
        # All tags that he used before show up
        completions = [tag for tag in
                       self.b.find_elements_by_css_selector('li.ui-menu-item a')]
        self.assertCountEqual([QUEEN, 'fish', 'pypo', 'boxing', 'bartender'], (tag.text for tag in completions))

        # He chooses the QUEEN tag
        for tag in completions:
            if tag.text == QUEEN:
                tag.click()
                break
        # And then submits the form
        self.b.find_element_by_id('submit-id-submit').click()

        # The new item was added and is the first item
        item = self.b.find_element_by_class_name('item_link')
        self.assertEqual(example_address, item.get_attribute('href'))

        # And QUEEN this is the only tag that was added
        taglist = self.b.find_element_by_css_selector('.tag-list')
        tags = [tag.text for tag in taglist.find_elements_by_css_selector('.tag')]
        self.assertEqual(tags, [QUEEN])

    def test_can_add_an_item_and_see_it_in_the_list(self):
        self.create_pre_authenticated_session()

        # User opens pypo and has no items in his list
        self.b.get(self.live_server_url)
        self.assertEqual(0, len(self.b.find_elements_by_class_name('item')))

        # He adds an item
        self.create_example_item()

        # The link is now in his list
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item was not added')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))

        # The domain is in the link text
        self.assertIn(u'[example.com]', items[0].text)

    def test_unable_to_add_duplicate(self):
        self.create_pre_authenticated_session()

        # User opens pypo and has no items in his list
        self.b.get(self.live_server_url)
        self.assertEqual(0, len(self.b.find_elements_by_class_name('item')))

        # He opens the add item page and sees the form
        self.b.get(self.live_server_url+'/add')

        # He submits a link
        self.create_example_item()

        # He submits the same link... again
        self.create_example_item('another-tag')

        tags = self._find_tags_from_detail()
        self.assertCountEqual(['super-tag', 'another-tag'], tags,
                              "Additional tag not added when trying to add a duplicate")

        # back to the index page
        self.b.get(self.live_server_url)
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Duplicate was added')

        # He can find the item with the new tag
        self.b.get(self.live_server_url+'/search/?q=another-tag')
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'New tag is not searchable')

    def test_added_items_are_searchable_by_tag(self):
        self.create_pre_authenticated_session()
        # Uther adds his usual item
        self.create_example_item()

        # Uther visits the search page and searches for the example page
        self.b.find_element_by_id('id_link_search').click()
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('super-tag')
        search_input.send_keys(Keys.ENTER)

        # He sees the example item with a link pointing to example.com
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item not found in results')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))
        self.assertIn('[example.com]', items[0].text)

    def test_added_items_are_searchable_by_domain(self):
        self.create_pre_authenticated_session()
        # He opens the add item page and sees the form
        self.create_example_item()

        # Uther visits the search page and searches for the example page
        self.b.find_element_by_id('id_link_search').click()
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('example.com')
        search_input.send_keys(Keys.ENTER)

        # He sees the example item with a link pointing to example.com
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item not found in results')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))
        self.assertIn('[example.com]', items[0].text)

    def test_invalid_searches_return_no_results(self):
        self.create_pre_authenticated_session()
        self._add_example_item()
        self.b.get(self.live_server_url)
        # Uther visits the search page and searches for an unknown term
        self.b.find_element_by_id('id_link_search').click()
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('invalid_search')
        search_input.send_keys(Keys.ENTER)

        # He sees no results
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(0, len(items))
        self.assertIn('No results found.',
                      (p.text for p in self.b.find_elements_by_tag_name('p')))

    def test_item_tags_are_shown_in_the_list(self):
        self.create_pre_authenticated_session()
        item = self._add_example_item()
        item.tags.add('example', 'fish')
        item.save()

        self.b.get(self.live_server_url)
        tag_string = ''.join(self._find_tags_from_detail())
        # Uther sees the two tags for his example entry in a list
        self.assertIn('example', tag_string)
        self.assertIn('fish', tag_string)

    def test_can_update_tags_from_the_list(self):
        self.session = self.create_pre_authenticated_session()
        self._add_example_item()
        self.b.get(self.live_server_url)
        # Uther visits the listing page and adds a new tag to the example item
        self.b.find_element_by_css_selector('.item-content .tools a.tags_link').click()
        tag_input = self.b.find_element_by_id('id_tags-tokenfield')
        # There are currently to tags for this item
        self.assertEqual('', tag_input.text)
        # Uther adds 2 new tags: example and fish
        tag_input.send_keys('example,fish,')
        tag_input.send_keys(Keys.ENTER)
        # The new tags are added to the list
        tags = self.b.find_elements_by_css_selector('.tag')
        tag_string = ''.join(t.text for t in tags)
        self.assertIn('example', tag_string)
        self.assertIn('fish', tag_string)

        self.b.find_element_by_id('id_link_search').click()
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('fish')
        search_input.send_keys(Keys.ENTER)

        # He sees the example item with a link pointing to example.com
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item not found in results')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))

    def find_tags_on_page(self):
        tags = {}
        for tag in self.b.find_elements_by_css_selector('.taglink'):
            tags[tag.find_element_by_css_selector('span.tagname').text] = int(
                tag.find_element_by_css_selector('span.count').text)
        return tags

    def test_facets_are_shown_in_a_search(self):
        self.create_pre_authenticated_session()
        # Uther added some of his tagged items
        self._add_tagged_items()

        # Another user also adds an item with the same tag
        add_item_for_new_user([QUEEN])

        # Uther starts a search for his queen-tagged items
        self.b.get(self.live_server_url+'/search')
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys(QUEEN)
        search_input.send_keys(Keys.ENTER)
        # He sees that his queen-tagged items also have other tags
        tags = self.find_tags_on_page()
        # And only those items that are shown are counted in the list of tags
        self.assertEqual({
            QUEEN: 3,
            'fish': 1,
            'bartender': 1,
            'pypo': 1
        }, tags)
        ## We are not testing the tag search link because that is haystacks responsibility

    def test_facets_are_shown_on_the_list_page(self):
        self.create_pre_authenticated_session()
        self._add_tagged_items()
        self.b.get(self.live_server_url)

        # On the main page there is a list of all of his tags
        tags = self.find_tags_on_page()
        self.assertEqual({
            QUEEN: 3,
            'boxing': 1,
            'fish': 2,
            'bartender': 1,
            'pypo': 1,
        }, tags)

    def test_list_that_is_filtered_by_tags(self):
        self.create_pre_authenticated_session()
        self._add_tagged_items()
        self.b.get(self.live_server_url)
        # Uther added his usual items and wants to see all of his queen-related entries
        # so he clicked on the tag on the index page
        queen_tag = self.b.find_element_by_css_selector('[data-tagname="{}"]'.format(QUEEN))
        queen_tag.click()
        # Now only the queen tagged items are shown
        tags = self.find_tags_on_page()
        self.assertEqual({
            QUEEN: 3,
            'fish': 1,
            'bartender': 1,
            'pypo': 1,
        }, tags)
        # He clicks on the fish tag and sees only the one item
        # that is tagged with queen and fish
        fish_tag = self.b.find_element_by_css_selector('[data-tagname="{}"]'.format('fish'))
        fish_tag.click()

        tags = self.find_tags_on_page()
        self.assertEqual({
            QUEEN: 1,
            'fish': 1,
        }, tags)

    def test_item_tags_link_to_the_tag_view(self):
        self.create_pre_authenticated_session()
        self._add_tagged_items()
        self.b.get(self.live_server_url)
        tag_links = self.b.find_elements_by_css_selector('a.tag')
        for tag in tag_links:
            self.assertTrue(tag.get_attribute('href').endswith(urlquote(tag.text)),
                            "Tag link doesn't end with the tag name: {} : {}".format(
                                tag.get_attribute('href'), tag.text
                            ))

    def test_default_protocol_for_url(self):
        self.create_pre_authenticated_session()
        self.b.get(self.live_server_url + '/add')
        # He pastes an url without protocol
        input_url = self.b.find_element_by_name('url')
        input_url.send_keys('www.example.com')
        # He "leaves" the url input field
        input_tags = self.b.find_element_by_id('id_tags-tokenfield')
        input_tags.click()
        # and the protocol is added to the url
        self.assertEqual('http://www.example.com', input_url.get_attribute('value'))

    def test_default_protocol_does_not_replace_protocol(self):
        self.create_pre_authenticated_session()
        self.b.get(self.live_server_url + '/add')
        # He pastes an url without protocol
        input_url = self.b.find_element_by_name('url')
        input_url.send_keys('https://www.example.com')
        # He "leaves" the url input field
        input_tags = self.b.find_element_by_id('id_tags-tokenfield')
        input_tags.click()
        # and the protocol is added to the url
        self.assertEqual('https://www.example.com', input_url.get_attribute('value'))