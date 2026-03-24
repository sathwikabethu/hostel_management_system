from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, TenantProfile, Room

class TenantRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_tenant = True
        if commit:
            user.save()
            TenantProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number')
            )
        return user
