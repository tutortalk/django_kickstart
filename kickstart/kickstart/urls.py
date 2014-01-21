from django.conf.urls import patterns, url, include
from . import views
from .forms import KickstartAuthenticationForm
from loginza.views import return_callback
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='home'),

    url(r'^login/?$', 'django.contrib.auth.views.login', {'authentication_form':KickstartAuthenticationForm}, 'custom-login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'custom-logout'),

    url(r'loginza/return_callback/$', return_callback, name='loginza_return'),
    url(r'^complete_loginza_registration/$', views.CompleteLoginzaRegistrationView.as_view(), name='complete_loginza_registration'),

    url(r'^register/$', views.KickstartRegistrationView.as_view(), name='kickstart_registration'),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^select2/', include('django_select2.urls')),
    url(r'^kickstart-admin/', include(admin.site.urls)),

    url(r'^profile/edit/$', views.ProfileEditView.as_view(), name='profile-edit'),
    url(r'^profile/avatar-upload/$', views.ProfileAvatarUploadView.as_view(), name='profile-avatar-upload'),
    url(r'^profile/avatar-delete/$', views.ProfileAvatarDeleteView.as_view(), name='profile-avatar-delete'),
    url(r'^profile/(?P<username>[^/]+)/$', views.ProfileView.as_view(), name='profile'),

    url(r'^project/create/$', views.ProjectCreateView.as_view(), name='project-create'),
    url(r'^project/donate/$', views.ProjectDonateView.as_view(), name='project-donate'),
    url(r'^project/(?P<slug_name>[^/]+)/$', views.ProjectDetailView.as_view(), name='project'),
    url(r'^project/(?P<project_id>[0-9]+)/publish/$', views.ProjectPublishView.as_view(), name='project-publish'),
    url(r'^project/(?P<project_id>[0-9]+)/edit/$', views.ProjectEditView.as_view(), name='project-edit'),
    url(r'^project/(?P<project_id>[0-9]+)/file-upload/$', views.ProjectFileUploadView.as_view(), name='project-file-upload'),
    url(r'^project/(?P<project_id>[0-9]+)/file/(?P<file_id>[0-9]+)/$', views.ProjectFileDeleteView.as_view(), name='project-file-delete'),
    url(r'^project/(?P<project_id>[0-9]+)/benefit/save/$', views.BenefitSaveView.as_view(), name='benefit-save'),
    url(r'^project/(?P<project_id>[0-9]+)/benefit/delete/$', views.BenefitDeleteView.as_view(), name='benefit-delete'),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
