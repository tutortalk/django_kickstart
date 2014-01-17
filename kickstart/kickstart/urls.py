from django.conf.urls import patterns, url, include
from . import views
from loginza.views import return_callback


urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),

    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'custom-logout'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'loginza/return_callback/$', return_callback, name='loginza_return'),
    url(r'^complete_loginza_registration/$', views.CompleteLoginzaRegistrationView.as_view(), name='complete_loginza_registration'),

    url(r'^register/$', views.KickstartRegistrationView.as_view(), name='kickstart_registration'),
    url(r'^accounts/', include('registration.backends.default.urls')),
)
