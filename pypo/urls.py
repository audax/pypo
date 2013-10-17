from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from rest_framework import routers
from haystack.views import search_view_factory, SearchView
from haystack.forms import SearchForm


from readme import views, account_urls
from readme.api import GroupViewSet, UserViewSet, ItemViewSet


admin.autodiscover()

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'items', ItemViewSet)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pypo.views.home', name='home'),
    # url(r'^pypo/', include('pypo.foo.urls')),

    url(r'^$', login_required(views.IndexView.as_view()), name='index'),
    url(r'^api/', include(router.urls)),
    url(r'^add/$', login_required(views.AddView.as_view()), name='item_add'),
    url(r'^view/(?P<pk>\d+)$', login_required(views.ItemView.as_view()), name='item_view'),
    url(r'^delete/(?P<pk>\d+)$', login_required(views.DeleteItem.as_view()), name='item_delete'),
    url(r'^accounts/', include(account_urls)),

    url(r'^search/', search_view_factory(
        view_class=SearchView,
        form_class=SearchForm
        ), name='haystack_search'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
