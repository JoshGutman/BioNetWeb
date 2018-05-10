from django import forms

#from django.contrib.auth.models import User
from  . import models
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext, gettext_lazy as _

class FileFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"), required=True)
    name = forms.CharField(label=_("Name"), max_length=40)
    organization = forms.CharField(label=_("Organization"), max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
    

    class Meta:
        model = models.MyUser
        fields = (
            'email',
            'name',
            'organization',
            'password1',
            'password2'
        )

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.name = self.cleaned_data['name']
        user.organization = self.cleaned_data['organization']

        if commit:
            user.save()
        return user

    '''
    def create_superuser(self, email, password):
        user = self.create_user(
            email,
            name=None,
            organization=None,
            password
        )

        user.is_admin = True
        user.save()
        return user
    '''
