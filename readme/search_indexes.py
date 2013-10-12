from haystack import indexes
from readme.models import Item


class ItemIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    readable_article = indexes.CharField(model_attr='readable_article')
    summary = indexes.CharField(model_attr='summary')
    title = indexes.CharField(model_attr='title')
    created = indexes.DateTimeField(model_attr='created')

    def get_model(self):
        return Item

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()