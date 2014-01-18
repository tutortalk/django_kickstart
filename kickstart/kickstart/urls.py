from django.conf.urls import patterns, url, include
from . import views
from .forms import KickstartAuthenticationForm
from loginza.views import return_callback


urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),

    url(r'^login/?$', 'django.contrib.auth.views.login', {'authentication_form':KickstartAuthenticationForm}, 'custom-login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'custom-logout'),

    url(r'loginza/return_callback/$', return_callback, name='loginza_return'),
    url(r'^complete_loginza_registration/$', views.CompleteLoginzaRegistrationView.as_view(), name='complete_loginza_registration'),

    url(r'^register/$', views.KickstartRegistrationView.as_view(), name='kickstart_registration'),
    url(r'^accounts/', include('registration.backends.default.urls')),

    url(r'^profile/edit/', views.ProfileEditView.as_view(), name='profile-edit'),
    url(r'^profile/(?P<username>[^/]+)/', views.ProfileView.as_view(), name='profile'),

    url(r'^project/create/', views.ProjectCreateView.as_view(), name='project-create'),
    url(r'^project/(?P<project_id>[0-9]+)/', views.ProjectEditView.as_view(), name='project-edit'),

    url(r'^select2/', include('django_select2.urls')),
)
