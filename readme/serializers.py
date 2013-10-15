from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from .models import Item

class TagListSerializer(serializers.WritableField):

    def from_native(self, data):
        if type(data) is not list:
            raise ParseError("expected a list of data")
        return data

    def to_native(self, obj):
        if type(obj) is not list:
            return [tag.name for tag in obj.all()]
        return obj

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class ItemSerializer(serializers.ModelSerializer):
    tags = TagListSerializer(required=False)
    title = serializers.CharField(required=False, read_only=True)
    readable_article = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = Item
        fields = ('id', 'url', 'title', 'created', 'readable_article', 'tags')
