from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url='/donate/')),
    url(r'^donate/', include('djstripe.urls', namespace="djstripe")),
    url(r'^admin/', include(admin.site.urls)),
)
