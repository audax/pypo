from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from tld import get_tld
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
from taggit.models import TagBase, ItemBase
from readme.download import download, DownloadException
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
        try:
            dl = download(self.url, max_content_length=settings.PYPO_MAX_CONTENT_LENGTH)
        except DownloadException:
            # TODO show a message that the download failed?
            self.title = self.url
            self.readable_article = None
        else:
            self.title, self.readable_article = parse(self, content_type=dl.content_type,
                                                  text=dl.text, content=dl.content)


class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    theme = models.CharField('Custom Theme', max_length=30, default=settings.PYPO_DEFAULT_THEME)
    can_invite = models.BooleanField(default=True)

@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, created, instance, **kwargs):
    if created:
        profile = UserProfile(user=instance)
        profile.save()