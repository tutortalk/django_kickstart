from django import forms
from .models import Profile, Project, Tag, Benefit, ProjectDonation, Comment
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
class DebugProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'short_desc', 'desc', 'amount', 'deadline', 'tags', 'is_public']

    deadline = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])
    tags = TagChoices(required=False)


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


@parsleyfy
class DonationForm(forms.ModelForm):
    class Meta:
        model = ProjectDonation
        fields = ['project', 'benefit']

        widgets = {'project': forms.widgets.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super(DonationForm, self).__init__(*args, **kwargs)
        self.fields['benefit'].queryset = self.instance.project.benefits.all()

    def clean_benefit(self):
        benefit = self.cleaned_data['benefit']
        user = self.instance.user
        project = self.instance.project

        if benefit.project != project:
            raise forms.ValidationError("Wrong project")

        if user.profile.balance < benefit.amount:
            raise forms.ValidationError("Not enough bucks on balance")


        return benefit

    def clean_project(self):
        project = self.cleaned_data['project']

        if not project.is_public:
            raise forms.ValidationError("Project is not published yet")

        return project


@parsleyfy
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['project', 'comment', 'parent']

        widgets = {
            'project': forms.widgets.HiddenInput(),
            'parent': forms.widgets.HiddenInput()
        }

    def clean_parent(self):
        comment = self.cleaned_data['parent']

        if comment and comment.project != self.cleaned_data['project']:
            raise forms.ValidationError("Wrong project")

        return comment
