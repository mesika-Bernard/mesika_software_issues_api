from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser
from ..utils import get_user_role  # For role display

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'gender', 'phone_number')

    def clean_groups(self):
        """Ensure exactly one group is assigned during user creation."""
        groups = self.cleaned_data.get('groups')
        if len(groups) != 1:
            raise forms.ValidationError("Exactly one group (role) must be assigned.")
        return groups

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'gender', 'phone_number')

    def clean_groups(self):
        """Ensure exactly one group is assigned during user update."""
        groups = self.cleaned_data.get('groups')
        if len(groups) != 1:
            raise forms.ValidationError("Exactly one group (role) must be assigned.")
        return groups

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'gender', 'phone_number', 'get_role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'gender')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'gender', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'gender', 'phone_number', 'groups'),
        }),
    )

    def get_role(self, obj):
        """Display the user's primary role in the admin list view."""
        return get_user_role(obj)
    get_role.short_description = 'Role'