from .models import Item
from conftest import QUEEN

EXAMPLE_COM = 'http://www.example.com/'

def test_unknown_tld():
    item = Item()
    item.url = 'foobar'
    assert item.domain is None


def test_find_items_by_tag(user, simple_items):
    assert {simple_items['item_fish'], simple_items['item_box']} == set(simple_items['filter'].tagged(QUEEN))


def test_find_items_by_multiple_tags(user, simple_items):
    assert simple_items['item_fish'] == simple_items['filter'].tagged(QUEEN, 'fish').get()
    assert simple_items['item_box'] == simple_items['filter'].tagged(QUEEN, 'box').get()


def test_chain_tag_filters(user, simple_items):
    assert simple_items['item_fish'] == simple_items['filter'].tagged(QUEEN).tagged('fish').get()
    assert simple_items['item_box'] == simple_items['filter'].tagged(QUEEN).tagged('box').get()


def test_filtering_out(user, tagged_items):
    tags = [QUEEN, 'fish']
    queryset = Item.objects.filter(owner_id=user.id).tagged(*tags)
    assert len(queryset) == 1, "Exactly one item with these tags should be found, but found: {}".format(
        '/ '.join("Item with tags {}".format(item.tags.names()) for item in queryset))


def test_excluding_tags(user, tagged_items):
    queryset = Item.objects.filter(owner_id=user.id).without(QUEEN)
    assert len(queryset) == 2

    queryset = Item.objects.filter(owner_id=user.id).tagged(QUEEN).without(QUEEN)
    assert len(queryset) == 0

def test_tag_names_property(user, simple_items):
    item = simple_items['item_fish']
    names = ["bar", "baz", "foo"]
    item.tag_names = names
    assert item.tag_names == names
