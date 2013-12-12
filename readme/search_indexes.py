from haystack import indexes
from readme.models import Item


class ItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    created = indexes.DateTimeField(model_attr='created')
    owner_id = indexes.IntegerField(model_attr='owner_id')
    tags = indexes.MultiValueField(faceted=True)

    def prepare_tags(self, obj):
        if not type(obj.tags) is list:
            return list(obj.tags.names())
        else:
            return obj.tags

    def get_model(self):
        return Item

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()