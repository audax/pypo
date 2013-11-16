from django.db import models
from readme.models import Item
from haystack import signals


class ItemOnlySignalProcessor(signals.BaseSignalProcessor):
    def setup(self):
        # Listen only to the ``User`` model.
        models.signals.post_save.connect(self.handle_save, sender=Item)
        models.signals.post_delete.connect(self.handle_delete, sender=Item)

    def teardown(self):
        # Disconnect only for the ``User`` model.
        models.signals.post_save.disconnect(self.handle_save, sender=Item)
        models.signals.post_delete.disconnect(self.handle_delete, sender=Item)
