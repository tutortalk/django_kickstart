from django import forms
from .models import Profile
from django.contrib.auth.forms import AuthenticationForm
from parsley.decorators import parsleyfy


@parsleyfy
class KickstartAuthenticationForm(AuthenticationForm):
    pass


@parsleyfy
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['last_name', 'first_name', 'about']


@parsleyfy
class DebugProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['last_name', 'first_name', 'about', 'balance']
