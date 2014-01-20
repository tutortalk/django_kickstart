from django.views.generic import TemplateView
from registration.backends.default.views import RegistrationView as TwoStepsRegistrationView
from .models import Profile, Project, Benefit, profile_avatar_dir
import loginza
from django.contrib import messages, auth
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from loginza.models import UserMap
from registration.views import RegistrationView as BaseRegistrationView

from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.views.generic.detail import DetailView
from parsley.decorators import parsleyfy
from .forms import ProfileForm, DebugProfileForm, ProjectForm, DebugProjectForm, BenefitForm

import datetime
import json
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden

import os
from .fineuploader import qqFileUploader


class KickstartRegistrationMixin(object):
    def create_profile(self, request, new_user, **cleaned_data):
        profile = Profile()
        profile.user = new_user
        profile.save()

    def get_form(self, form_class):
        form_class = parsleyfy(form_class)
        form = super(KickstartRegistrationMixin, self).get_form(form_class)

        return form


class KickstartRegistrationView(KickstartRegistrationMixin, TwoStepsRegistrationView):
    def register(self, request, **cleaned_data):
        user = super(KickstartRegistrationView, self).register(request, **cleaned_data)
        self.create_profile(request, user, **cleaned_data)

        return user


class CompleteLoginzaRegistrationView(KickstartRegistrationMixin, BaseRegistrationView):
    template_name = "registration/loginza_registration_form.html"
    disallowed_url = reverse_lazy('home')

    def get_usermap(self, request):
        identity_id = request.session.get('users_complete_reg_id', None)
        user_map = UserMap.objects.get(identity__id=identity_id)

        return user_map

    def registration_allowed(self, request):
        if request.user.is_authenticated():
            return False
        
        try:
            self.get_usermap(request)

            return True
        
        except UserMap.DoesNotExist:
            return False

    def register(self, request, **cleaned_data):
        user_map = self.get_usermap(request)
    
        user = user_map.user
        user.username = cleaned_data['username']
        user.email = cleaned_data['email']
        user.save()
    
        self.create_profile(request, user, **cleaned_data)
        user_map.verified = True
        user_map.save()

        user = auth.authenticate(user_map=user_map)
        auth.login(request, user)
        del request.session['users_complete_reg_id']

        return user

    def get_success_url(self, request, user):
        return reverse('home')


def loginza_error_handler(sender, error, **kwargs):
    messages.error(sender, error.message)

loginza.signals.error.connect(loginza_error_handler)


def loginza_auth_handler(sender, user, identity, **kwargs):
    try:
        # it's enough to have single identity verified to treat user as verified
        UserMap.objects.get(user=user, verified=True)
        auth.login(sender, user)

    except UserMap.DoesNotExist:
        sender.session['users_complete_reg_id'] = identity.id
        return redirect(reverse('complete_loginza_registration'))

loginza.signals.authenticated.connect(loginza_auth_handler)


class LoginRequiredMixin(object):
    u"""Ensures that user must be authenticated in order to access view."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class JSONResponseMixin(object):
    def json_response(self, context):
        return HttpResponse(json.dumps(context), content_type='application/json')


class HomeView(TemplateView):
    template_name = "home.html"


class ProfileView(DetailView):
    model = Profile
    slug_field = 'user__username'
    slug_url_kwarg = 'username'
    template_name = 'profile/detail.html'
    context_object_name = 'profile'


class ProfileEditView(LoginRequiredMixin, FormView):
    form_class = DebugProfileForm if settings.DEBUG else ProfileForm
    success_message = "Changes successfully saved"
    template_name = 'profile/edit.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ProfileEditView, self).get_context_data(*args, **kwargs)
        context['profile'] = self.request.user.profile

        return context

    def get_form_kwargs(self):
        kwargs = super(ProfileEditView, self).get_form_kwargs()
        kwargs['instance'] = self.request.user.profile

        return kwargs

    def form_valid(self, form):
        form.save()
        result = super(ProfileEditView, self).form_valid(form)

        return result

    def get_success_url(self):
        return reverse('profile-edit')


class ProfileAvatarUploadView(LoginRequiredMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        profile = request.user.profile

        relative_upload_path = profile_avatar_dir(profile, self.request.POST.get('qqfilename', None))
        absolute_upload_path = os.path.join(settings.MEDIA_ROOT, relative_upload_path)
        upload_dir = os.path.dirname(absolute_upload_path)
        filename = os.path.basename(absolute_upload_path)

        uploader = qqFileUploader(request, uploadDirectory=upload_dir, allowedExtensions=[".jpg", ".jpeg", ".png"], sizeLimit=2147483648)
        result = uploader.handleUpload(filename)

        if not 'error' in result:
            profile.avatar = relative_upload_path
            profile.save()
            result['image'] = profile.avatar.url

        return self.json_response(result)


class ProfileAvatarDeleteView(LoginRequiredMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
         profile = request.user.profile
         profile.avatar.delete()
         profile.save()

         return self.json_response({'success': True})


class ProjectOwnerMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_id'])
        if self.project.user_id != request.user.pk:
            return HttpResponseForbidden()

        return super(ProjectOwnerMixin, self).dispatch(request, *args, **kwargs)


class ProjectDetailView(DetailView):
    model = Project
    slug_field = 'slug_name'
    slug_url_kwarg = 'slug_name'
    template_name = 'project/detail.html'
    context_object_name = 'project'


class ProjectCreateView(LoginRequiredMixin, FormView):
    form_class = ProjectForm
    template_name = 'project/create.html'

    def get_form_kwargs(self):
        kwargs = super(ProjectCreateView, self).get_form_kwargs()
        kwargs['instance'] = Project(user=self.request.user)
        init_date = timezone.now() + datetime.timedelta(days=31)
        kwargs['initial']['deadline'] = init_date.strftime('%Y-%m-%d %H:%M:%S')

        return kwargs

    def form_valid(self, form):
        form.save()

        return super(ProjectCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('profile', args=(self.request.user, ))


class ProjectEditView(LoginRequiredMixin, ProjectOwnerMixin, FormView):
    form_class = DebugProjectForm if settings.DEBUG else ProjectForm
    template_name = 'project/edit.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectEditView, self).get_context_data(*args, **kwargs)
        context['project'] = self.project

        return context

    def get_form_kwargs(self):
        kwargs = super(ProjectEditView, self).get_form_kwargs()
        kwargs['instance'] = self.project

        return kwargs

    def form_valid(self, form):
        form.save()

        return super(ProjectEditView, self).form_valid(form)

    def get_success_url(self):
        return reverse('profile', args=(self.request.user, ))


class ProjectPublishView(LoginRequiredMixin, ProjectOwnerMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        self.project.is_public = True
        self.project.save()

        return self.json_response({'success': True})


class BenefitSaveView(LoginRequiredMixin, ProjectOwnerMixin, FormView, JSONResponseMixin, View):
    form_class = BenefitForm

    def get_form_kwargs(self):
        kwargs = super(BenefitSaveView, self).get_form_kwargs()
        benefit_id = self.request.POST.get('benefit_id', None)

        if benefit_id:
            benefit = Benefit.objects.get(pk=benefit_id, project=self.project)

        else:
            benefit = Benefit(project=self.project)

        kwargs['instance'] = benefit

        return kwargs

    def form_valid(self, form):
        benefit = form.save()
        return self.json_response({'success': True, 'benefit_id': benefit.pk})

    def form_invalid(self, form):
        return self.json_response({'success': False})


class BenefitDeleteView(LoginRequiredMixin, ProjectOwnerMixin, JSONResponseMixin, View):
    def post(self, request, **kwargs):
        benefit_id = request.POST.get('benefit_id', None)
        benefit = get_object_or_404(Benefit, pk=benefit_id)
        if self.project.pk != benefit.project_id:
            return HttpResponseForbidden()

        benefit.delete()

        return self.json_response({'success': True})
