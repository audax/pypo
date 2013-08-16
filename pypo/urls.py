from django.conf.urls import patterns, include, url
from django.contrib import admin

from readme import views

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pypo.views.home', name='home'),
    # url(r'^pypo/', include('pypo.foo.urls')),

    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^add/$', views.AddView.as_view(), name='item_add'),
    url(r'^view/(?P<pk>\d+)$', views.ItemView.as_view(), name='item_view'),


    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
