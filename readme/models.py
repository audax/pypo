from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.functional import cached_property
from tld import get_tld
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
from taggit.models import TagBase, ItemBase
from readme.download import download
from readme.scrapers import parse

import logging

request_log = logging.getLogger('readme.requests')


class ItemQuerySet(models.query.QuerySet):

    def tagged(self, *tags):
        filtered = self
        for tag in tags:
            filtered = filtered.filter(tags__name=tag)
        return filtered


class ItemManager(models.Manager):

    def get_queryset(self):
        return ItemQuerySet(self.model)

    def __getattr__(self, name, *args):
        if name.startswith("_"):
            raise AttributeError
        return getattr(self.get_query_set(), name, *args)

class ItemTag(TagBase):

    def slugify(self, tag, i=None):
        return tag

class TaggedItem(ItemBase):

    tag = models.ForeignKey(ItemTag, related_name="%(app_label)s_%(class)s_items")
    content_object = models.ForeignKey('Item')

    @classmethod
    def tags_for(cls, model, instance=None):
        if instance is not None:
            return cls.tag_model().objects.filter(**{
                '%s__content_object' % cls.tag_relname(): instance
            })
        return cls.tag_model().objects.filter(**{
            '%s__content_object__isnull' % cls.tag_relname(): False
        }).distinct()

class Item(models.Model):
    """
    Entry in the read-it-later-list

    """
    #:param url Page url
    url = models.URLField(max_length=2000)
    #:param title Page title
    title = models.TextField()
    #:param created Creating date of the item
    created = models.DateTimeField(auto_now_add=True)
    #:param owner Owning user
    owner = models.ForeignKey(User)
    #:param readable_article Processed content of the url
    readable_article = models.TextField(null=True)
    #:param tags User assigned tags
    tags = TaggableManager(blank=True, through=TaggedItem)

    objects = ItemManager()

    @cached_property
    def summary(self):
        '''
        Shortened artile
        '''
        summary = strip_tags(self.readable_article)[:300]
        if len(summary) == 300:
            # utf-8 elipse
            summary += ' …'
        return summary

    @cached_property
    def domain(self):
        """
        Domain of the url
        """
        return get_tld(self.url, fail_silently=True)

    def get_absolute_url(self):
        return reverse('item_view', args=[str(self.id)])

    def get_api_url(self):
        return '/api/items/{}/'.format(str(self.id))

    def get_update_url(self):
        return reverse('item_update', args=[str(self.id)])

    def get_tag_names(self):
        return self.tags.values_list('name', flat=True)

    def fetch_article(self):
        """
        Fetches a title and a readable_article for the current url.
        It uses the scrapers module for this and only downloads the content.
        """
        dl = download(self.url, max_content_length=settings.PYPO_MAX_CONTENT_LENGTH)
        self.title, self.readable_article = parse(self, content_type=dl.content_type,
                                                  text=dl.text, content=dl.content)

