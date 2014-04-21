from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import generic
from django.conf import settings
from haystack.forms import FacetedSearchForm
from haystack.query import SearchQuerySet
from haystack.views import FacetedSearchView, search_view_factory
from .models import Item
from .forms import CreateItemForm, UpdateItemForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import redirect, render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json


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
    context_object_name = 'item_list'

    def get_queryset(self):
        return Item.objects.filter(owner=self.request.user).order_by('-created').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        facets = SearchQuerySet().filter(owner_id=self.request.user.id).facet('tags').facet_counts()
        tag_objects = []
        for name, count in facets.get('fields', {}).get('tags', []):
            if name is not None:
                tag_objects.append(Tag(name, count, []))
        context['tags'] = tag_objects

        paginator = Paginator(context['item_list'], settings.PYPO_ITEMS_ON_PAGE)
        try:
            page = paginator.page(self.request.GET.get('page'))
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        context['current_item_list'] = page
        return context


class Tag:
    def __init__(self, name, count, tag_list):
        self.name = name
        self.count = count
        self.tag_list = tag_list[:]
        if not name in self.tag_list:
            self.tag_list.append(name)
        self.url = reverse('tags', kwargs={'tags': ','.join(self.tag_list)})

    def as_tuple(self):
        return self.name, self.count, self.url

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())


@login_required
def tags(request, tags=''):
    if tags == '':
        return redirect(reverse('index'))
    tag_list = [tag for tag in tags.split(',') if tag != '']

    # Due to a bug (or feature?) in Whoosh or haystack, we can't filter for all tags at once,
    # the .filter(tags=[...]) method cannot handle spaces apparently
    # It however works with tags__in, but that is an OR
    sqs = SearchQuerySet().filter(owner_id=request.user.id)
    for tag in tag_list:
        sqs = sqs.filter(tags__in=[tag])
    sqs = sqs.order_by('-created').facet('tags')

    facets = sqs.facet_counts()
    result_objects = [result.object for result in sqs]
    tag_objects = [Tag(name, count, tag_list) for name, count in facets.get('fields', {}).get('tags', [])]
    return render_to_response('readme/item_list.html', {
        'current_item_list': result_objects,
        'tags': tag_objects,
        'user': request.user,
    })


class DeleteItemView(RestrictItemAccessMixin, generic.DeleteView):
    model = Item
    context_object_name = 'item'
    success_url = reverse_lazy('index')


class TagNamesToContextMixin:

    def get_context_data(self, **kwargs):
        context = super(TagNamesToContextMixin, self).get_context_data(**kwargs)

        sqs = SearchQuerySet().filter(owner_id=self.request.user.id).facet('tags')

        facets = sqs.facet_counts()
        tags = [name for name, count in facets.get('fields', {}).get('tags', []) if name is not None]
        context['tags'] = json.dumps(tags)
        return context


class UpdateItemView(TagNamesToContextMixin, RestrictItemAccessMixin, generic.UpdateView):
    model = Item
    context_object_name = 'item'
    success_url = reverse_lazy('index')

    form_class = UpdateItemForm

    def form_valid(self, form):
        self.object = form.save()
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())



class AddView(TagNamesToContextMixin, LoginRequiredMixin, generic.CreateView):
    model = Item
    success_url = reverse_lazy('index')

    form_class = CreateItemForm

    def form_valid(self, form):
        self.object = form.save(commit=False)

        duplicates = Item.objects.filter(owner=self.request.user, url=self.object.url)
        if duplicates.count():
            duplicate = duplicates[0]
            duplicate.tags.add(*form.cleaned_data["tags"])
            # additional save to update the search index
            duplicate.save()
            return HttpResponseRedirect(duplicate.get_absolute_url())
        self.object.owner = self.request.user
        self.object.fetch_article()
        self.object.save()
        form.save_m2m()
        # additional save to update the search index
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        url = self.request.GET.get('url', None)
        return {'url': url}


class ItemView(RestrictItemAccessMixin, generic.DetailView):
    model = Item
    context_object_name = 'item'


class ItemSearchView(FacetedSearchView):
    """
    SearchView that passes a dynamic SearchQuerySet to the
    form that restricts the result to those owned by
    the current user.
    """

    def build_form(self, form_kwargs=None):
        user_id = self.request.user.id
        self.searchqueryset = SearchQuerySet().filter(owner_id=user_id).facet('tags')
        return super(ItemSearchView, self).build_form(form_kwargs)

search = login_required(search_view_factory(
    view_class=ItemSearchView,
    form_class=FacetedSearchForm,
))


def test(request, test_name):
    if settings.DEBUG:
        return render_to_response('readme/tests/{}.html'.format(test_name))
    else:
        return redirect(reverse('index'))


# Class based views as normal view function

index = IndexView.as_view()
add = AddView.as_view()
view = ItemView.as_view()
delete = DeleteItemView.as_view()
update = UpdateItemView.as_view()
