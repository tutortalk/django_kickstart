from django import forms
from .models import Profile, Project, Tag, Benefit
from django.contrib.auth.forms import AuthenticationForm
from parsley.decorators import parsleyfy
from django_select2 import AutoModelSelect2TagField


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


class TagChoices(AutoModelSelect2TagField):
    queryset = Tag.objects
    search_fields = ['name__icontains']

    def get_model_field_values(self, value):
        return {'name': value }


@parsleyfy
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'short_desc', 'desc', 'amount', 'deadline', 'tags']

    deadline = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])
    tags = TagChoices(required=False)


@parsleyfy
class BenefitForm(forms.ModelForm):
    class Meta:
        model = Benefit
        fields = ['amount', 'text']

        widgets = {
            'text': forms.widgets.TextInput()
        }
