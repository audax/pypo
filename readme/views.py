from django.views import generic
from haystack.forms import SearchForm
from haystack.views import SearchView, search_view_factory
from .models import Item
from .forms import CreateItemForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class LoginRequiredMixin(object):
    """
    Mixing for generic views

    It applies the login_required decorator
    """
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class RestrictItemAccessMixin(object):
    """
    Mixing for generic views that implement get_object()

    Restricts access so that every user can only access views for
    objects that have him as the object.owner
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user == self.get_object().owner:
            return redirect('index')
        return super(RestrictItemAccessMixin, self).dispatch(request, *args, **kwargs)


class IndexView(LoginRequiredMixin, generic.ListView):
    context_object_name = 'current_item_list'

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user).order_by('-created')


class DeleteItem(RestrictItemAccessMixin, generic.DeleteView):
    model = Item
    context_object_name = 'item'
    success_url = reverse_lazy('index')


class AddView(LoginRequiredMixin, generic.CreateView):
    model = Item
    success_url = reverse_lazy('index')

    form_class = CreateItemForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        try:
            self.object = self.model.objects.get(url=self.object.url, owner=self.request.user)
        except Item.DoesNotExist:
            self.object.owner = self.request.user
        else:
            self.object.tags.clear()
            self.object.tags.add(*form.cleaned_data['tags'])

        self.object.fetch_article()

        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        url = self.request.GET.get('url', None)
        return {'url': url}


class ItemView(RestrictItemAccessMixin, generic.DetailView):
    model = Item
    context_object_name = 'item'

search = login_required(search_view_factory(
        view_class=SearchView,
        form_class=SearchForm
))

# Class based views as normal view function

index = IndexView.as_view()
add = AddView.as_view()
view = ItemView.as_view()
delete = DeleteItem.as_view()