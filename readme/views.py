from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from .models import Item


class IndexView(generic.ListView):
    context_object_name = 'current_item_list'

    def get_queryset(self):
        return Item.objects.order_by('-created')


class AddView(generic.CreateView):
    model = Item
    success_url = "/"

class ItemView(generic.DetailView):
    model = Item
    
        