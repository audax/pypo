from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    url = models.URLField()
    title = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User)

