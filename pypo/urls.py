from django.conf.urls import patterns, include, url
from django.contrib import admin

from readme import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'pypo.views.home', name='home'),
    # url(r'^pypo/', include('pypo.foo.urls')),

    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^add/$', views.AddView.as_view(), name='index'),
    url(r'^view/(?P<pk>\d+)$', views.ItemView.as_view(), name='index'),


    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
