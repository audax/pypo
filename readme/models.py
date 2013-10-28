from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.conf import settings
from tld import get_tld
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
from readability import Document
from readability.readability import Unparseable

import requests
import logging
from readme.scrapers import parse

request_log = logging.getLogger('readme.requests')


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
            req = requests.get(url, stream=True)
            try:
                content_length = int(req.headers.get('content-length', 0))
            except ValueError:
                # no valid content length set
                self._fetch_fallback()
            else:
                # if content is too long, abort.
                if content_length > settings.PYPO_MAX_CONTENT_LENGTH:
                    request_log.info('Aborting: content-length %d is larger than max content length %d',
                                     content_length, settings.PYPO_MAX_CONTENT_LENGTH)
                    self._fetch_fallback()
                    return
                # In case content_length lied to us
                content = req.iter_content(settings.PYPO_MAX_CONTENT_LENGTH).next()
                text = None
                # only decode text requests
                if req.headers.get('content-type', '').startswith('text/'):
                    try:
                        text = content.decode(req.encoding)
                    except UnicodeDecodeError:
                        # just ignore it then, the encoding from the header was wrong
                        pass

        except requests.RequestException:
            text, content = None, None

        self.title, self.readable_article = parse(self, content_type=req.headers.get('content-type', ''),
                                                  text=text, content=content)

