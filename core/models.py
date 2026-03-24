from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_tenant = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.username

class Room(models.Model):
    ROOM_TYPES = (
        ('AC', 'AC'),
        ('NON_AC', 'Non-AC'),
    )
    room_number = models.CharField(max_length=10, unique=True)
    capacity = models.IntegerField(default=1)
    occupants = models.IntegerField(default=0)
    fee_per_month = models.DecimalField(max_digits=8, decimal_places=2)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='NON_AC')
    
    @property
    def is_full(self):
        return self.occupants >= self.capacity

    def __str__(self):
        return f"Room {self.room_number}"

class TenantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class FeePayment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
    )
    METHOD_CHOICES = (
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Cash', 'Cash'),
    )
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_tenant': True})
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    month = models.DateField(auto_now_add=True)
    date_paid = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES, blank=True)
    
    def __str__(self):
        return f"{self.tenant.username} - {self.amount} - {self.status}"

class Complaint(models.Model):
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    )
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_tenant': True})
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Open')
    
    def __str__(self):
        return self.title

class Visitor(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_tenant': True})
    visitor_name = models.CharField(max_length=100)
    purpose = models.CharField(max_length=200)
    visit_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return f"Visitor for {self.tenant.username}: {self.visitor_name}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Feedback(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_tenant': True})
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    remarks = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback from {self.tenant.username}"

class WeeklyMenu(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')
    ]
    day = models.CharField(max_length=15, choices=DAY_CHOICES, unique=True)
    breakfast = models.CharField(max_length=255, default='Not Set')
    lunch = models.CharField(max_length=255, default='Not Set')
    dinner = models.CharField(max_length=255, default='Not Set')
    
    def __str__(self):
        return f"{self.day} Menu"
