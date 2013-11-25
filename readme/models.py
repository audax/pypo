from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.conf import settings
from tld import get_tld
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
from readme.download import download
from readme.scrapers import parse

import requests
import logging

request_log = logging.getLogger('readme.requests')


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
    tags = TaggableManager(blank=True)

    @property
    def summary(self):
        '''
        Shortened artile
        '''
        return strip_tags(self.readable_article)[:300]

    @property
    def domain(self):
        """
        Domain of the url
        """
        return get_tld(self.url, fail_silently=True)

    def get_absolute_url(self):
        return reverse('item_view', args=[str(self.id)])

    def get_delete_url(self):
        return reverse('item_delete', args=[str(self.id)])

    def get_update_url(self):
        return reverse('item_update', args=[str(self.id)])

    def fetch_article(self):
        """
        Fetches a title and a readable_article for the current url.
        It uses the scrapers module for this and only downloads the content.
        """
        dl = download(self.url, max_content_length=settings.PYPO_MAX_CONTENT_LENGTH)
        self.title, self.readable_article = parse(self, content_type=dl.content_type,
                                                  text=dl.text, content=dl.content)

