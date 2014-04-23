from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from .models import Item

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class ItemSerializer(serializers.ModelSerializer):
    tags = serializers.Field(source='get_tag_names')
    title = serializers.CharField(required=False)
    readable_article = serializers.CharField(required=False)

    class Meta:
        model = Item
        fields = ('id', 'url', 'title', 'created', 'readable_article', 'tags')
