from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from .serializers import UserSerializer, GroupSerializer, ItemSerializer
from .models import Item, fetch_article


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Items to be viewed or edited.
    """
    serializer_class = ItemSerializer
    model = Item

    def get_queryset(self):
        """
        Filter Items by the current user
        """
        return Item.objects.filter(owner=self.request.user)

    def pre_save(self, item):
        """
        Prepare the item for saving

        Set the items user to the current user, fetch the
        article title and readable_article

        If the url was already fetched by this user, overwrite the old Item
        """
        item.owner = self.request.user
        item.title, item.readable_article = fetch_article(item.url)


    def post_save(self, item, *args, **kwargs):
        """
        Special treatment of the tag attribute
        """
        if type(item.tags) is list:
            # If tags were provided in the request
            saved_bookmark = Item.objects.get(pk=item.pk)
            for tag in item.tags:
                saved_bookmark.tags.add(tag)

