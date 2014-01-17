from django.views.generic import TemplateView
from registration.backends.default.views import RegistrationView as TwoStepsRegistrationView
from .models import Profile
import loginza
from django.contrib import messages, auth
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import redirect
from loginza.models import UserMap
from registration.views import RegistrationView as BaseRegistrationView



class KickstartRegistrationMixin(object):
    def create_profile(self, request, new_user, **cleaned_data):
        profile = Profile()
        profile.user = new_user
        profile.save()


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


class HomeView(TemplateView):
    template_name = "home.html"
