from django.conf.urls import patterns, url, include
from . import views

urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),

    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'custom-logout'),
    url(r'^accounts/', include('django.contrib.auth.urls')),

    url(r'^register/$', views.KickstartRegistrationView.as_view(), name='kickstart_registration'),
    url(r'^accounts/', include('registration.backends.default.urls')),
)
