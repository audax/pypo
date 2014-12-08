from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import Item

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class TagSerializer(serializers.Field):
    def to_representation(self, data):
        return data
        
    def to_internal_value(self, obj):
        return sorted(obj)

class ItemSerializer(serializers.ModelSerializer):
    tags = TagSerializer(source='tag_names') 
    title = serializers.CharField(required=False)
    readable_article = serializers.CharField(required=False)
    class Meta:
        model = Item
        fields = ('id', 'url', 'title', 'created', 'readable_article', 'tags')
        
    def create(self, validated_data):
        tags = validated_data.pop('tag_names')
        item = Item(**validated_data)
        item.fetch_article()
        item.save()
        item.tag_names = tags
        item.save()
        return item
