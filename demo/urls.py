from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url='/donations')),
    # url(r'^blog/', include('blog.urls')),
    #url(r'^donations/', include('donations.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile', RedirectView.as_view(url='/donations')),
    url(r'^accounts/logout', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^donations/', include('djstripe.urls', namespace="djstripe")),
    url(r'^admin/', include(admin.site.urls)),
)
