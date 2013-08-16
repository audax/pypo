from django.db import models
from django.contrib.auth.models import User
from django.utils.html import strip_tags


class Item(models.Model):
    url = models.URLField()
    title = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User)

    readable_article = models.TextField(null=True)

    @property
    def summary(self):
        return strip_tags(self.readable_article)[:300]

