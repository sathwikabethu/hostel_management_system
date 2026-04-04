from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Room, TenantProfile, FeePayment, Announcement, Feedback, VisitorProfile, VisitRequest, VisitLog, ComplaintPoll, PollVote, PollEvidence

admin.site.register(User, UserAdmin)
admin.site.register(Room)
admin.site.register(TenantProfile)
admin.site.register(FeePayment)
admin.site.register(ComplaintPoll)
admin.site.register(PollVote)
admin.site.register(PollEvidence)
admin.site.register(Announcement)
admin.site.register(Feedback)
admin.site.register(VisitorProfile)
admin.site.register(VisitRequest)
admin.site.register(VisitLog)
