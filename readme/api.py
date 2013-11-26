from rest_framework import viewsets
from .serializers import ItemSerializer
from .models import Item


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
        return Item.objects.filter(owner=self.request.user).order_by('created')

    def pre_save(self, item):
        """
        Prepare the item for saving

        Set the items user to the current user, fetch the
        article title and readable_article

        If the url was already fetched by this user, overwrite the old Item
        """
        item.owner = self.request.user
        item.fetch_article()


    def post_save(self, item, *args, **kwargs):
        """
        Special treatment of the tag attribute
        """
        if type(item.tags) is list:
            # If tags were provided in the request
            saved_bookmark = Item.objects.get(pk=item.pk)
            for tag in item.tags:
                saved_bookmark.tags.add(tag)
            # refresh search index
            item.save()

