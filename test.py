import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hostel_project.settings")
django.setup()

from core.models import User, TenantProfile
from core.forms import TenantRegistrationForm

print("--- ADMIN LOGIN TEST ---")
try:
    users = User.objects.filter(username__iexact='admin')
    print("Found admin users:", users)
    for u in users:
        print(u.username, "PWD OK:", u.check_password('admin123'))
except Exception as e:
    print('Admin error', e)

print("--- REGISTRATION ERROR TEST ---")
try:
    data = {
        'username': 'testuser123',
        'password1': 'SomeStrongPassword123!',
        'password2': 'SomeStrongPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'guardian_name': 'Guardian',
        'guardian_phone': '0987654321'
    }
    f = TenantRegistrationForm(data)
    if f.is_valid():
        u = f.save()
        print("Registration Succeeded!", u.username)
    else:
        print("Form errors:", f.errors)
except Exception as e:
    import traceback
    traceback.print_exc()
