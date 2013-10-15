from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from tld import get_tld
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
from readability import Document
from readability.readability import Unparseable

import requests


class Item(models.Model):
    url = models.URLField(max_length=2000)
    title = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User)
    readable_article = models.TextField(null=True)
    tags = TaggableManager(blank=True)

    @property
    def summary(self):
        return strip_tags(self.readable_article)[:300]

    @property
    def domain(self):
        return get_tld(self.url.encode('utf-8'), fail_silently=True)

    def get_absolute_url(self):
        return reverse('item_view', args=[str(self.id)])

    def get_delete_url(self):
        return reverse('item_delete', args=[str(self.id)])

    def fetch_article(self):
        url = self.url
        try:
            req = requests.get(url)
        except requests.RequestException:
            self._fetch_fallback()
        else:
            if 'html' in req.headers['content-type']:
                self._parse_webpage(req)
                return
            else:
                self._fetch_fallback()

    def _fetch_fallback(self):
        self.title, self.readable_article = self.url, ''

    def _parse_webpage(self, req):
        try:
            doc = Document(req.text)
        except Unparseable:
            self._fetch_fallback()
        else:
            self.title, self.readable_article = doc.short_title(), doc.summary(True)
            return


