from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('tenant', 'Tenant'),
        ('parent', 'Parent'),
        ('visitor', 'Visitor'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='tenant')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    registered_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @property
    def is_tenant(self):
        return self.role == 'tenant'
        
    @property
    def is_parent(self):
        return self.role == 'parent'

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
        
    @property
    def is_visitor(self):
        return self.role == 'visitor'

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

class RoomRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.tenant.username} - Room {self.room.room_number} ({self.status})"

class TenantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='child_tenants', limit_choices_to={'role': 'parent'})
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class VisitorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='visitor_profile')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_visitors', limit_choices_to={'role': 'tenant'})

    def __str__(self):
        return f"Visitor: {self.user.username} for Tenant: {self.tenant.username}"

class VisitRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('no-show', 'No-Show'),
    )
    visitor = models.ForeignKey(VisitorProfile, on_delete=models.CASCADE, related_name='visit_requests')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_visit_requests', limit_choices_to={'role': 'tenant'})
    
    visit_date = models.DateField()
    visit_time_slot = models.CharField(max_length=50)
    expected_duration = models.CharField(max_length=50)
    purpose = models.CharField(max_length=200)
    number_of_accompanying_persons = models.IntegerField(default=0)
    
    request_status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='visit_approvals', limit_choices_to={'role': 'admin'})
    rejection_reason = models.TextField(null=True, blank=True)
    tenant_flag_note = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"Visit by {self.visitor.user.username} on {self.visit_date}"

class VisitLog(models.Model):
    STATUS_CHOICES = (
        ('expected', 'Expected'),
        ('checked-in', 'Checked-In'),
        ('checked-out', 'Checked-Out'),
        ('no-show', 'No-Show'),
    )
    visit_request = models.OneToOneField(VisitRequest, on_delete=models.CASCADE, related_name='log')
    actual_checkin_time = models.DateTimeField(null=True, blank=True)
    actual_checkout_time = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkins_handled', limit_choices_to={'role': 'admin'})
    log_status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='expected')

    def __str__(self):
        return f"Log for VR #{self.visit_request.id} - {self.log_status}"

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
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'tenant'})
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    month = models.DateField(auto_now_add=True)
    date_paid = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES, blank=True)
    
    def __str__(self):
        return f"{self.tenant.username} - {self.amount} - {self.status}"

class ComplaintPoll(models.Model):
    POLL_CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Cleanliness', 'Cleanliness'),
        ('Maintenance', 'Maintenance'),
        ('Noise', 'Noise'),
        ('Facilities', 'Facilities'),
        ('Safety', 'Safety'),
        ('Other', 'Other')
    ]
    DURATION_CHOICES = [
        (1, '1 day'),
        (3, '3 days'),
        (7, '7 days')
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('withdrawn', 'Withdrawn')
    ]
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('none', 'None')
    ]

    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_polls')
    complaint_title = models.CharField(max_length=100)
    complaint_category = models.CharField(max_length=20, choices=POLL_CATEGORY_CHOICES)
    complaint_description = models.TextField() # min 20, max 500
    poll_question = models.TextField()
    poll_duration_days = models.IntegerField(choices=DURATION_CHOICES)
    poll_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    vote_yes_count = models.IntegerField(default=0)
    vote_no_count = models.IntegerField(default=0)
    raised_at = models.DateTimeField(auto_now_add=True)
    closes_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_polls')
    admin_action_note = models.TextField(null=True, blank=True)
    priority_flag = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='none')

    class Meta:
        db_table = 'complaint_polls'

    def __str__(self):
        return f"{self.complaint_title} ({self.poll_status})"

class PollVote(models.Model):
    VOTE_CHOICES = [('yes', 'Yes'), ('no', 'No')]
    poll = models.ForeignKey(ComplaintPoll, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    vote = models.CharField(max_length=3, choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'poll_votes'
        unique_together = ('poll', 'voter')

class PollEvidence(models.Model):
    poll = models.ForeignKey(ComplaintPoll, on_delete=models.CASCADE, related_name='evidence')
    file_url = models.FileField(upload_to='poll_evidence/')
    file_type = models.CharField(max_length=50, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'poll_evidence'

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Feedback(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'tenant'})
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
