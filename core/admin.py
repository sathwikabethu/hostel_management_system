from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Room, TenantProfile, FeePayment, Complaint, Visitor, Announcement, Feedback

admin.site.register(User, UserAdmin)
admin.site.register(Room)
admin.site.register(TenantProfile)
admin.site.register(FeePayment)
admin.site.register(Complaint)
admin.site.register(Visitor)
admin.site.register(Announcement)
admin.site.register(Feedback)
