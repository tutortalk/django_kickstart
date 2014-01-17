from django.views.generic import TemplateView
from registration.backends.default.views import RegistrationView as TwoStepsRegistrationView
from .models import Profile


class KickstartRegistrationView(TwoStepsRegistrationView):
    def create_profile(self, request, new_user, **cleaned_data):
        profile = Profile()
        profile.user = new_user
        profile.save()

    def register(self, request, **cleaned_data):
        user = super(KickstartRegistrationView, self).register(request, **cleaned_data)
        self.create_profile(request, user, **cleaned_data)

        return user


class HomeView(TemplateView):
    template_name = "home.html"

