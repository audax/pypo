from django.views import generic
from .models import Item
from .forms import CreateItemForm
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User

class IndexView(generic.ListView):
    context_object_name = 'current_item_list'

    def get_queryset(self):
        return Item.objects.order_by('-created')


class AddView(generic.CreateView):
    model = Item
    success_url = "/"

    form_class = CreateItemForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())




class ItemView(generic.DetailView):
    model = Item
