import pytest
from functools import partial

from .models import Item, User

QUEEN = 'queen-without-spaces-but_umläuts'
EXAMPLE_COM = 'http://www.example.com/'

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


@pytest.mark.django_db
class TestBasic:

    def test_item_user_relation(self, user):
        item = Item()
        item.url = 'http://www.example.com'
        item.title = 'Title'
        item.owner = user
        item.save()
        assert item.owner

    def test_unknown_tld(self):
        item = Item()
        item.url = 'foobar'
        assert item.domain is None


@pytest.mark.django_db
class TestItemModel:

    def _add_simple_example_items(self, user):
        self.item_fish = add_example_item(user, [QUEEN, 'fish', 'cookie'])
        self.item_box = add_example_item(user, [QUEEN, 'box'])
        self.filter = Item.objects.filter(owner_id=user.id)

    def test_find_items_by_tag(self, user):
        self._add_simple_example_items(user)
        assert {self.item_fish, self.item_box} == set(self.filter.tagged(QUEEN))

    def test_find_items_by_multiple_tags(self, user):
        self._add_simple_example_items(user)
        assert self.item_fish == self.filter.tagged(QUEEN, 'fish').get()
        assert self.item_box == self.filter.tagged(QUEEN, 'box').get()

    def test_chain_tag_filters(self, user):
        self._add_simple_example_items(user)
        assert self.item_fish == self.filter.tagged(QUEEN).tagged('fish').get()
        assert self.item_box == self.filter.tagged(QUEEN).tagged('box').get()

    def test_filtering_out(self, user):
        add_tagged_items(user)

        tags = [QUEEN, 'fish']
        queryset = Item.objects.filter(owner_id=user.id).tagged(*tags)
        assert len(queryset) == 1, "Exactly one item with these tags should be found, but found: {}".format(
            '/ '.join("Item with tags {}".format(item.tags.names()) for item in queryset))

