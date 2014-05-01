from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()

readme_patterns = patterns('readme.views',
    url(r'^$', 'index', name='index'),
    url(r'^tags/(?P<tags>.*)$', 'tags', name='tags'),
    url(r'^add/$', 'add', name='item_add'),
    url(r'^update/(?P<pk>\d+)/$', 'update', name='item_update'),
    url(r'^view/(?P<pk>\d+)/$', 'view', name='item_view'),
    url(r'^search/', 'search', name='haystack_search'),
    url(r'^invite/$', 'invite', name='invite'),
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^test/(?P<test_name>\w+)$', 'test', name='test_view'),
)


urlpatterns = patterns('',
    url(r'^accounts/', include('readme.account_urls')),
    url(r'^api/', include('readme.api_urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
) + readme_patterns
