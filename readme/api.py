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
        return Item.objects.filter(owner=self.request.user).order_by('-created').prefetch_related('tags')

    def perform_create(self, serializer):
        """
        Pass the current user to the serializer
        """
        serializer.save(owner=self.request.user)


