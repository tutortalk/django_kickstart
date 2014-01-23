from django.views.generic import TemplateView
from registration.backends.default.views import RegistrationView as TwoStepsRegistrationView
from .models import Profile, Project, ProjectDonation, ProjectFile, Benefit, Comment, profile_avatar_dir, project_file_dir
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
from django.views.generic.list import ListView
from parsley.decorators import parsleyfy
from .forms import ProfileForm, DebugProfileForm, ProjectForm, DebugProjectForm, BenefitForm, DonationForm, CommentForm

import datetime
import json
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden

import os
from .fineuploader import qqFileUploader
from django.template import loader, RequestContext


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


class AjaxUploadMixin(object):
    def handle_upload(self, request, relative_upload_dir, allowed_extensions=None):
        uploader = qqFileUploader(
            request,
            uploadDirectory=os.path.join(settings.MEDIA_ROOT, relative_upload_dir),
            allowedExtensions=allowed_extensions,
            sizeLimit=2147483648
        )
        result = uploader.handleUpload()

        return uploader.getUploadName(), result


class HomeView(ListView):
    template_name = "home.html"
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        search = self.request.GET.get('search', None)
        if search:
            return Project.objects.search_projects(search)

        else:
            return Project.objects.get_all_projects()


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


class ProfileAvatarUploadView(LoginRequiredMixin, AjaxUploadMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        profile = request.user.profile
        profile.clear_avatar()
        relative_upload_dir = profile_avatar_dir(profile)
        uploaded_file_name, result = self.handle_upload(request, relative_upload_dir, allowed_extensions=[".jpg", ".jpeg", ".png"])

        if not 'error' in result:
            profile.avatar = os.path.join(relative_upload_dir, uploaded_file_name)
            profile.save()
            result['image'] = profile.get_avatar()

        return self.json_response(result)


class ProfileAvatarDeleteView(LoginRequiredMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
         profile = request.user.profile
         profile.clear_avatar()

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

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        project = context['project']
        donations = project.get_donations()

        if self.request.user.is_authenticated():
            if len([d for d in donations if d.user_id == self.request.user.pk]) == 0:
                donation = ProjectDonation(project=project, user=self.request.user)
                context['donation_form'] = DonationForm(instance=donation)

        collected_amount = 0
        for donation in donations:
            collected_amount += donation.benefit.amount

        context.update({
            'collected_amount': collected_amount,
            'donations': donations,
            'comments': project.comments.select_related('user').all(),
            'comment_form': CommentForm(initial={'project': project})
        })

        return context


class ProjectDonateView(LoginRequiredMixin, JSONResponseMixin, FormView):
    form_class = DonationForm

    def get_form_kwargs(self):
        kwargs = super(ProjectDonateView, self).get_form_kwargs()
        project = Project.objects.get(pk=self.request.POST.get('project', None))
        kwargs['instance'] = ProjectDonation(project=project, user=self.request.user)

        return kwargs

    def form_valid(self, form):
        form.save()

        return self.json_response({'success': True})

    def form_invalid(self, form):
        errors_strings = []
        for error in form.errors.values():
            errors_strings.append('<br>'.join(error))

        return self.json_response({'success': False, 'errors': '<br>'.join(errors_strings)})


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


class ProjectFileUploadView(LoginRequiredMixin, ProjectOwnerMixin, AjaxUploadMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        project = self.project
        project_file = ProjectFile(project=project)

        relative_upload_dir = project_file_dir(project_file)
        uploaded_file_name, result = self.handle_upload(request, relative_upload_dir)

        if not 'error' in result:
            project_file.original_filename = request.REQUEST.get('qqfilename', None)
            filename, ext = os.path.splitext(project_file.original_filename)
            project_file.ext = ext
            project_file.file = os.path.join(relative_upload_dir, uploaded_file_name)
            project_file.save()
            rendered_file = loader.render_to_string('project/file_preview.html', {'file': project_file}, RequestContext(request))
            result['file'] = rendered_file

        return self.json_response(result)


class ProjectFileDeleteView(LoginRequiredMixin, ProjectOwnerMixin, JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        project = self.project
        project_file = get_object_or_404(ProjectFile, pk=kwargs['file_id'], project=project)
        project_file.delete()

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


class CommentSaveView(LoginRequiredMixin, FormView, JSONResponseMixin, View):
    form_class = CommentForm

    def get_form_kwargs(self):
        kwargs = super(CommentSaveView, self).get_form_kwargs()
        kwargs['instance'] = Comment(user=self.request.user)

        return kwargs

    def form_valid(self, form):
        comment = form.save()
        return self.json_response({'success': True, 'comment_id': comment.pk})

    def form_invalid(self, form):
        print form.errors
        return self.json_response({'success': False})


class BenefitDeleteView(LoginRequiredMixin, ProjectOwnerMixin, JSONResponseMixin, View):
    def post(self, request, **kwargs):
        benefit_id = request.POST.get('benefit_id', None)
        benefit = get_object_or_404(Benefit, pk=benefit_id)
        if self.project.pk != benefit.project_id:
            return HttpResponseForbidden()

        benefit.delete()

        return self.json_response({'success': True})
