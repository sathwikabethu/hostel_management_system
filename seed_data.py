import os
import django
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hostel_project.settings")
django.setup()

from django.utils import timezone
from core.models import User, Room, TenantProfile, FeePayment, Announcement

def seed():
    print("Seeding database...")
    
    # Create Rooms
    r1, _ = Room.objects.get_or_create(room_number='101', defaults={'capacity': 2, 'fee_per_month': 500, 'room_type': 'AC'})
    r2, _ = Room.objects.get_or_create(room_number='102', defaults={'capacity': 3, 'fee_per_month': 400, 'room_type': 'NON_AC'})
    r3, _ = Room.objects.get_or_create(room_number='103', defaults={'capacity': 1, 'fee_per_month': 800, 'room_type': 'AC'})

    # Create Admin
    admin_user, _ = User.objects.get_or_create(username='admin', defaults={
        'first_name': 'Hostel', 'last_name': 'Admin', 'role': 'admin', 'status': 'approved', 'is_superuser': True, 'is_staff': True
    })
    admin_user.set_password('admin123')
    admin_user.save()

    # Create Tenants
    def create_tenant(username, first_name, last_name, room):
        user, created = User.objects.get_or_create(username=username, defaults={
            'first_name': first_name, 'last_name': last_name, 'role': 'tenant', 'status': 'approved', 'is_active': True
        })
        if created:
            user.set_password('password123')
            user.save()
            TenantProfile.objects.create(user=user, phone_number='1234567890', room=room)
            room.occupants += 1
            room.save()
        return user

    t1 = create_tenant('alice', 'Alice', 'Smith', r1)
    t2 = create_tenant('bob', 'Bob', 'Johnson', r1)
    t3 = create_tenant('charlie', 'Charlie', 'Brown', r2)

    # Create Fee Payments
    FeePayment.objects.get_or_create(tenant=t1, amount=500, status='Paid', payment_method='UPI', month=date.today() - timedelta(days=5))
    FeePayment.objects.get_or_create(tenant=t2, amount=500, status='Paid', payment_method='Card', month=date.today() - timedelta(days=2))
    FeePayment.objects.get_or_create(tenant=t3, amount=400, status='Pending', month=date.today())

    # Create Announcements
    Announcement.objects.get_or_create(title='Hostel Maintenance', content='Water supply will be cut off for 2 hours tomorrow afternoon for cleaning.')
    Announcement.objects.get_or_create(title='Rent Due Reminder', content='Please ensure timely payment of your monthly hostel fee via the portal.')

    print("Database successfully seeded with realistic dummy data!")

if __name__ == '__main__':
    seed()
