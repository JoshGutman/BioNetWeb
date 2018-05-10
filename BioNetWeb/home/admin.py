from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, ReadOnlyPasswordHashField
from django import forms
from django.utils.translation import gettext, gettext_lazy as _

from .models import MyUser

'''
class MyUserInline(admin.StackedInline):
    model = MyUser
    can_delete = False
    verbose_name_plural = 'myuser'

    fields = ('email', 'name', 'organization')
'''

'''
class MyUserAdmin(admin.ModelAdmin):
    #inlines = [MyUserInline]
    pass
'''

'''
class MyUserChangeForm(UserChangeForm):
    
    class Meta(UserChangeForm.Meta):
        model=MyUser
        fields = ('email', 'name', 'organization', 'can_use_monsoon')
'''

class MyUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using "
            "<a href=\"{}\">this form</a>."
        ),
    )

    class Meta:
        model = MyUser
        fields = '__all__'
        #field_classes = {UserModel.USERNAME_FIELD: 'email'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get('password')
        if password:
            password.help_text = password.help_text.format('../password/')
        user_permissions = self.fields.get('user_permissions')
        if user_permissions:
            user_permissions.queryset = user_permissions.queryset.select_related('content_type')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

'''
class MyUserAdmin(UserAdmin):
    model = MyUser
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'organization')}),
        (_('Permissions'), {'fields': ('can_use_monsoon',)}),
    )
    add_fieldsets = ()
    form = MyUserChangeForm
    list_display = ('email', 'name', 'organization')
    list_filter = ('can_use_monsoon', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'name', 'organization')
    ordering = ('email', 'name', 'organization')
    filter_horizontal = ('groups', 'user_permissions',)
'''

@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    model = MyUser
    add_form_template = 'admin/auth/user/add_form.html'
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'organization')}),
        (_('Permissions'), {'fields': ('can_use_monsoon',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = MyUserChangeForm
    list_display = ('email', 'name', 'organization')
    list_filter = ('can_use_monsoon', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'name', 'organization')
    ordering = ('email', 'name', 'organization')
    filter_horizontal = ('groups', 'user_permissions',)


# Register your models here.
#admin.site.register(MyUser, MyUserAdmin)
