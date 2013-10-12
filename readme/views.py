from django.views import generic
from .models import Item
from .forms import CreateItemForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from readability import Document
import requests


class IndexView(generic.ListView):
    context_object_name = 'current_item_list'

    def get_queryset(self):
        return Item.objects.order_by('-created')


class DeleteItem(generic.DeleteView):
    model = Item
    context_object_name = 'item'
    success_url = reverse_lazy('index')


class AddView(generic.CreateView):
    model = Item
    success_url = "/"

    form_class = CreateItemForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            self.object = self.model.objects.get(url=self.object.url, owner=self.request.user)
        except Item.DoesNotExist:
            pass

        self.object.owner = self.request.user
        try:
            req = requests.get(self.object.url)
        except requests.RequestException:
            self.object.title = self.object.url
            self.object.readable_article = ''
        else:
            doc = Document(req.text)
            self.object.title = doc.short_title()
            self.object.readable_article = doc.summary(True)

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class ItemView(generic.DetailView):
    model = Item
    context_object_name = 'item'
