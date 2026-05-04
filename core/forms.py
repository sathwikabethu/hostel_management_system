from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User, TenantProfile, Room, name_validator

class TenantRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, validators=[name_validator])
    last_name = forms.CharField(max_length=30, required=True, validators=[name_validator])
    phone_number = forms.CharField(max_length=15, required=True)

    guardian_name = forms.CharField(max_length=100, required=True)
    guardian_phone = forms.CharField(max_length=15, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'tenant'
        user.status = 'pending'
        user.is_active = False
        if commit:
            user.save()
            TenantProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                guardian_name=self.cleaned_data['guardian_name'],
                guardian_phone=self.cleaned_data['guardian_phone']
            )
        return user

class ParentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, validators=[name_validator])
    last_name = forms.CharField(max_length=30, required=True, validators=[name_validator])
    phone_number = forms.CharField(max_length=15, required=True)
    child_username = forms.CharField(max_length=150, required=True, help_text="Enter your child's (tenant's) username")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name')

    def clean_child_username(self):
        username = self.cleaned_data.get('child_username')
        try:
            tenant_user = User.objects.get(username=username, role='tenant')
            if hasattr(tenant_user, 'tenant_profile') and tenant_user.tenant_profile.parent is not None:
                raise forms.ValidationError("This tenant already has a registered parent.")
            self.cleaned_data['tenant_user'] = tenant_user
        except User.DoesNotExist:
            raise forms.ValidationError("No tenant found with this username.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'parent'
        user.status = 'pending'
        user.is_active = False
        if commit:
            user.save()
            profile = self.cleaned_data['tenant_user'].tenant_profile
            profile.parent = user
            profile.save()
        return user

class VisitorRegistrationForm(forms.ModelForm):
    tenant_username = forms.CharField(label="Tenant's Username", help_text="Enter the username of the tenant you are visiting.", max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'validators': [name_validator]}),
            'last_name': forms.TextInput(attrs={'validators': [name_validator]}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].validators.append(name_validator)
        self.fields['last_name'].validators.append(name_validator)

    def clean_tenant_username(self):
        username = self.cleaned_data.get('tenant_username')
        try:
            tenant_user = User.objects.get(username=username, role='tenant')
            self.cleaned_data['tenant_user'] = tenant_user
            return username
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid tenant username. Please verify the person you are visiting.")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'visitor'
        user.status = 'pending'
        user.is_active = False
        if commit:
            user.save()
            # Create VisitorProfile
            from .models import VisitorProfile
            VisitorProfile.objects.create(
                user=user,
                tenant=self.cleaned_data['tenant_user']
            )
        return user
