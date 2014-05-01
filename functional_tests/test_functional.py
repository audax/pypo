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
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from sitegate.models import InvitationCode

from pypo import settings
from readme.models import Item
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

@override_settings(
    HAYSTACK_CONNECTIONS=TEST_INDEX,
    STATICFILES_STORAGE='pipeline.storage.PipelineStorage',
    PIPELINE_ENABLED=False)
class ExistingUserTest(PypoLiveServerTestCase):
    fixtures = ['initial_data.json']

    def wait_until(self, callback, timeout=10):
        from selenium.webdriver.support.wait import WebDriverWait
        WebDriverWait(self.b, timeout).until(callback)

    def setUp(self):
        self.b = getattr(webdriver,  os.environ.get('WEBDRIVER', 'Firefox'))()
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

    def create_pre_authenticated_session(self, create_session=True):
        session = SessionStore()
        session[SESSION_KEY] = self.user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session.save()
        ## to set a cookie we need to first visit the domain.
        ## 404 pages load the quickest!
        if create_session:
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
        input_tags = self.b.find_element_by_id('id_tags')
        input_tags.click()
        input_tags.send_keys(tags)
        input_tags.send_keys(',')
        self.b.find_element_by_id('submit-id-submit').click()

    def test_autocomplete_tags(self):
        self.skipTest('Only broken on travis, works locally')
        example_address = 'http://foobar.local/'
        self.create_pre_authenticated_session()
        self._add_tagged_items()
        self.b.get(self.live_server_url + '/add')

        input_url = self.b.find_element_by_name('url')
        input_url.send_keys(example_address)

        self.b.find_element_by_css_selector('input.select2-input').click()

        completions = self.b.find_elements_by_css_selector('.select2-result-label')
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

        domains = self.b.find_elements_by_class_name('item_domain')
        # The domain is next to the link text
        self.assertIn(u'[example.com]', domains[0].text)

    def test_can_delete_item_with_popover_confirmation(self):
        self.create_pre_authenticated_session()

        # User opens pypo and has no items in his list
        self.b.get(self.live_server_url)
        self.assertEqual(0, len(self.b.find_elements_by_class_name('item')))

        # He adds an item
        self.create_example_item()

        # The link is now in his list
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item was not added')

        self.b.find_element_by_class_name('delete_link').click()

        # popover opens
        self.assertTrue(self.b.find_element_by_class_name('popover'))

        # Confirm the deletion
        self.b.find_element_by_class_name('confirm-dialog-btn-confirm').click()

        # Meta: the fadeOut is not tested because that is just ugly in selenium and
        # not worth it.

        # Item is deleted after reloading
        self.b.get(self.live_server_url)
        self.assertEqual(0, len(self.b.find_elements_by_class_name('item')))


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
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('super-tag')
        search_input.send_keys(Keys.ENTER)

        # He sees the example item with a link pointing to example.com
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item not found in results')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))

        domains = self.b.find_elements_by_class_name('item_domain')
        # The domain is next to the link text
        self.assertIn('[example.com]', domains[0].text)

    def test_search_field_in_nav_bar(self):
        self.create_pre_authenticated_session()
        # Uther adds his usual item
        self.create_example_item()

        # Uther starts a search with the search bar in the navbar
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('super-tag')
        search_input.send_keys(Keys.ENTER)

        # He sees the example item with a link pointing to example.com
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item not found in results')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))

    def test_added_items_are_searchable_by_domain(self):
        self.create_pre_authenticated_session()
        # He opens the add item page and sees the form
        self.create_example_item()

        # Uther visits the search page and searches for the example page
        search_input = self.b.find_element_by_name('q')
        search_input.send_keys('example.com')
        search_input.send_keys(Keys.ENTER)

        # He sees the example item with a link pointing to example.com
        items = self.b.find_elements_by_class_name('item_link')
        self.assertEqual(1, len(items), 'Item not found in results')
        self.assertEqual(EXAMPLE_COM, items[0].get_attribute('href'))

        domains = self.b.find_elements_by_class_name('item_domain')
        # The domain is next to the link text
        self.assertIn('[example.com]', domains[0].text)

    def test_invalid_searches_return_no_results(self):
        self.create_pre_authenticated_session()
        self._add_example_item()
        self.b.get(self.live_server_url)
        # Uther visits the search page and searches for an unknown term
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
        input_tags = self.b.find_element_by_id('id_tags')
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
        input_tags = self.b.find_element_by_id('id_tags')
        input_tags.click()
        # and the protocol is added to the url
        self.assertEqual('https://www.example.com', input_url.get_attribute('value'))

    def test_can_update_title(self):
        item = self._add_example_item([])
        item_id = item.id

        self.create_pre_authenticated_session()
        self.b.get(self.live_server_url)

        # Uther actives the edit mode
        self.b.find_element_by_id('id_enable_editable').click()

        # and clicks on the title of the first element
        self.b.find_element_by_css_selector('.item_link').click()

        title_input = self.b.find_element_by_css_selector('.editable-input input')
        self.assertEqual(title_input.get_attribute('value'), item.title)
        title_input.send_keys('-foobar')
        title_input.send_keys(Keys.ENTER)

        self.wait_until(
            lambda b: b.find_element_by_css_selector('.item_link').text == item.title + '-foobar')

        updated_item = Item.objects.get(pk=item_id)
        self.assertEqual(updated_item.title, item.title+'-foobar')

    def test_can_update_description(self):
        item = self._add_example_item([])
        item_id = item.id

        self.create_pre_authenticated_session()
        self.b.get(self.live_server_url)

        # Uther actives the edit mode
        self.b.find_element_by_id('id_enable_editable').click()

        # and clicks on the description of the first element
        self.b.find_element_by_css_selector('.item_description').click()

        description_input = self.b.find_element_by_css_selector('.editable-input textarea')
        description_input.send_keys('-foobar')

        self.b.find_element_by_css_selector('button.editable-submit').click()

        self.wait_until(
            lambda b: b.find_element_by_css_selector('.item_description').text == '-foobar')

        updated_item = Item.objects.get(pk=item_id)
        self.assertEqual(updated_item.readable_article, '-foobar')

    def test_can_update_tags(self):
        self.skipTest('Only broken on travis, works locally')
        item = self._add_example_item([])
        item_id = item.id

        self.create_pre_authenticated_session()
        self.b.get(self.live_server_url)

        # Uther actives the edit mode
        self.b.find_element_by_id('id_enable_editable').click()

        # and clicks on the description of the first element
        self.b.find_element_by_css_selector('.tag-list').click()

        tag_input = self.b.find_element_by_css_selector('input.select2-input')
        tag_input.send_keys('test,foobar')
        # first enter to complete the tag
        tag_input.send_keys(Keys.ENTER)
        # the second to submit the form
        tag_input.send_keys(Keys.ENTER)

        self.wait_until(
            lambda b: b.find_element_by_css_selector('.tag-list').text == 'test, foobar')

        updated_item = Item.objects.get(pk=item_id)
        self.assertEqual(set(updated_item.tags.names()), {'test', 'foobar'})

    def test_can_invite_a_friend(self):
        self.create_pre_authenticated_session()
        # Uther wants to invite his friend Hans to pypo

        # he opens the invite-page
        self.b.get(self.live_server_url+'/invite')

        # and creates a new invite code
        self.b.find_element_by_id('id_create_invite').submit()

        code = self.b.find_element_by_class_name('invite_code').text

        # and logs out
        self.b.find_element_by_id('id_link_logout').click()


        self.b.get(self.live_server_url)

        self.b.find_element_by_id('id_code').send_keys(code)
        self.b.find_element_by_id('id_email').send_keys('testmail@localhost.lan')
        password_input = self.b.find_element_by_id('id_password1')
        password_input.send_keys('dev')
        password_input.send_keys(Keys.ENTER)

        # he is now registered, logged in and can create an item
        self.assertTrue(self.b.find_element_by_id('id_link_add'))
        self.create_example_item()

        # and logs out
        self.b.find_element_by_id('id_link_logout').click()

        # Uther logs back in
        self.create_pre_authenticated_session(create_session=False)

        # he opens the invite-page
        self.b.get(self.live_server_url+'/invite')

        # and sees Hans' username in the table
        self.assertEqual('testmail@localhost.lan',
                         self.b.find_element_by_class_name('invite_acceptor').text)

    def test_can_delete_free_invite_codes(self):
        self.create_pre_authenticated_session()

        # Uther created an invitation code that he now wants to delete,
        # he also has an expired code
        valid_code = InvitationCode.add(self.user)
        expired_code = InvitationCode.add(self.user)
        expired_code.expired = True
        expired_code.save()

        codes = [expired_code.code, valid_code.code]

        # he opens the invite-page
        self.b.get(self.live_server_url+'/invite')

        # sees both codes
        self.assertEqual(codes, [c.text for c in self.b.find_elements_by_class_name('invite_code')])

        # and deletes the first code
        self.b.find_element_by_id('id_delete_code_{}'.format(valid_code.id)).submit()

        # now only the expired code is left
        self.assertEqual([expired_code.code],
                         [c.text for c in self.b.find_elements_by_class_name('invite_code')])

        # which he can't delete
        with self.assertRaises(NoSuchElementException):
            self.b.find_element_by_class_name('delete_code')


