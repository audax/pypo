from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()

readme_patterns = patterns('readme.views',
    url(r'^$', 'index', name='index'),
    url(r'^add/$', 'add', name='item_add'),
    url(r'^view/(?P<pk>\d+)/$', 'view', name='item_view'),
    url(r'^delete/(?P<pk>\d+)/$', 'delete', name='item_delete'),
    url(r'^search/', 'search', name='haystack_search'),
)


urlpatterns = patterns('',
    url(r'^accounts/', include('readme.account_urls')),
    url(r'^api/', include('readme.api_urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
) + readme_patterns
