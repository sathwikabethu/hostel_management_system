from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum
from .forms import TenantRegistrationForm, ParentRegistrationForm, VisitorRegistrationForm
from django.contrib.auth.decorators import login_required
from .decorators import admin_required, tenant_required, parent_required
from .models import User, Room, Announcement, TenantProfile, FeePayment, VisitRequest, VisitorProfile, VisitLog, ComplaintPoll, PollVote, PollEvidence
from .utils import evaluate_active_polls
from datetime import timedelta
from django.utils import timezone
# Auth Views
def register_parent_view(request):
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            messages.success(request, 'Registration successful. Please wait for admin approval.')
            return redirect('login')
    else:
        form = ParentRegistrationForm()
    return render(request, 'auth/register_parent.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please wait for admin approval.')
            return redirect('login')
    else:
        form = TenantRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def register_visitor_view(request):
    if request.method == 'POST':
        form = VisitorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please wait for admin approval.')
            return redirect('login')
    else:
        form = VisitorRegistrationForm()
    return render(request, 'auth/register_visitor.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        try:
            user_obj = User.objects.get(username=u)
            if user_obj.check_password(p):
                if user_obj.status == 'rejected':
                    messages.error(request, "Your registration has been declined. Please contact support.")
                elif not user_obj.is_active or user_obj.status == 'pending':
                    messages.error(request, "Your account is awaiting admin approval. You will be notified once approved.")
                else:
                    login(request, user_obj)
                    if user_obj.role == 'admin' or user_obj.is_superuser:
                        return redirect('admin_dashboard')
                    elif user_obj.role == 'parent':
                        return redirect('parent_dashboard')
                    elif user_obj.role == 'visitor':
                        return redirect('visitor_dashboard')
                    else:
                        return redirect('tenant_dashboard')
            else:
                messages.error(request, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
        except User.DoesNotExist:
            messages.error(request, "Please enter a correct username and password. Note that both fields may be case-sensitive.")
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def home_view(request):
    return render(request, 'index.html')

def elevate_me(request):
    if request.user.is_authenticated:
        request.user.is_admin = True
        request.user.is_superuser = True
        request.user.is_tenant = False
        request.user.save()
        return redirect('admin_dashboard')
    return redirect('login')

# --- Admin Dash & Features ---
@login_required
@admin_required
def admin_dashboard(request):
    if request.method == 'POST' and 'title' in request.POST:
        title, content = request.POST.get('title'), request.POST.get('content')
        if title and content:
            Announcement.objects.create(title=title, content=content)
            messages.success(request, "Announcement posted.")
            return redirect('admin_dashboard')
    revenue = FeePayment.objects.filter(status='Paid').aggregate(Sum('amount'))['amount__sum'] or 0
    stats = {
        'tenants_count': User.objects.filter(role='tenant').count(),
        'rooms_count': Room.objects.count(),
        'complaints_count': ComplaintPoll.objects.filter(poll_status='active').count(),
        'revenue': revenue
    }
    recent_tenants = User.objects.filter(role='tenant', is_active=True).order_by('-date_joined')[:5]
    pending_users = User.objects.filter(is_active=False).order_by('-date_joined')
    pending_visits = VisitRequest.objects.filter(request_status='pending').order_by('visit_date')
    announcements = Announcement.objects.all().order_by('-date_posted')
    return render(request, 'admin/admin_dashboard.html', {
        'stats': stats, 
        'recent_tenants': recent_tenants,
        'pending_users': pending_users,
        'pending_visits': pending_visits,
        'announcements': announcements
    })

@login_required
@admin_required
def approve_user(request, user_id):
    if request.method == 'POST':
        u = get_object_or_404(User, id=user_id)
        action = request.POST.get('action')
        if action == 'approve':
            u.is_active = True
            u.status = 'approved'
            u.save()
            print(f"NOTIFY USER: Your account has been approved. You may now log in.")
            messages.success(request, f"Account for {u.username} has been approved.")
        elif action == 'reject':
            reason = request.POST.get('reason', '')
            u.status = 'rejected'
            u.rejection_reason = reason
            u.is_active = False
            u.save()
            print(f"NOTIFY USER: Your registration has been declined.")
            messages.success(request, f"Registration for {u.username} was rejected.")
    return redirect('admin_dashboard')

@login_required
@admin_required
def approve_visit_request(request, v_id):
    if request.method == 'POST':
        vr = get_object_or_404(VisitRequest, id=v_id)
        action = request.POST.get('action')
        if action == 'approve':
            vr.request_status = 'approved'
            vr.reviewed_by = request.user
            vr.save()
            VisitLog.objects.create(visit_request=vr, log_status='expected')
            print(f"NOTIFY VISITOR: Your visit on {vr.visit_date} has been approved.")
            print(f"NOTIFY TENANT: A visit by {vr.visitor.user.username} on {vr.visit_date} is confirmed.")
            messages.success(request, f"Visit request approved.")
        elif action == 'reject':
            vr.request_status = 'rejected'
            vr.rejection_reason = request.POST.get('reason', '')
            vr.reviewed_by = request.user
            vr.save()
            print(f"NOTIFY VISITOR: Your visit request for {vr.visit_date} has been declined.")
            messages.success(request, f"Visit request rejected.")
    return redirect('admin_dashboard')

@login_required
@admin_required
def delete_announcement(request, a_id):
    if request.method == 'POST':
        a = get_object_or_404(Announcement, id=a_id)
        a.delete()
        messages.success(request, "Announcement disabled & deleted.")
    return redirect('admin_dashboard')

@login_required
@admin_required
def manage_rooms(request):
    if request.method == 'POST':
        if 'allocate' in request.POST:
            tenant_id = request.POST.get('tenant_id')
            room_id = request.POST.get('room_id')
            if tenant_id and room_id:
                tenant = User.objects.get(id=tenant_id)
                room = Room.objects.get(id=room_id)
                if room.occupants < room.capacity:
                    profile = tenant.tenant_profile
                    profile.room = room
                    profile.save()
                    room.occupants += 1
                    room.save()
                    messages.success(request, f"Allocated {tenant.username} to Room {room.room_number}")
                else:
                    messages.error(request, "Room is full!")
        elif 'r_num' in request.POST:
            r_num, r_cap, r_fee, r_type = request.POST.get('r_num'), request.POST.get('r_cap'), request.POST.get('r_fee'), request.POST.get('r_type')
            Room.objects.create(room_number=r_num, capacity=r_cap, fee_per_month=r_fee, room_type=r_type)
            messages.success(request, "Room added!")
        return redirect('manage_rooms')

    from django.db.models import F
    available_rooms = Room.objects.filter(occupants__lt=F('capacity'))
    unassigned_tenants = User.objects.filter(role='tenant', tenant_profile__room__isnull=True)

    return render(request, 'admin/manage_rooms.html', {
        'rooms': Room.objects.all(),
        'available_rooms': available_rooms,
        'unassigned_tenants': unassigned_tenants
    })

@login_required
@admin_required
def manage_complaints(request):
    evaluate_active_polls()
    
    if request.method == 'POST':
        poll_id = request.POST.get('poll_id')
        action = request.POST.get('action')
        poll = get_object_or_404(ComplaintPoll, id=poll_id)
        
        if action == 'resolve':
            note = request.POST.get('admin_action_note')
            if len(note) < 20:
                messages.error(request, "Resolution note must be at least 20 characters.")
                return redirect('manage_complaints')
            poll.poll_status = 'resolved'
            poll.admin_action_note = note
            poll.resolved_by = request.user
            poll.resolved_at = timezone.now()
            poll.save()
            print(f"NOTIFY TENANT ({poll.raised_by.username}) & VOTERS: Poll '{poll.complaint_title}' has been resolved. Note: {note}")
            messages.success(request, "Poll resolved successfully.")
            
        elif action == 'dismiss':
            reason = request.POST.get('dismissal_reason')
            if not reason:
                messages.error(request, "Dismissal reason is required.")
                return redirect('manage_complaints')
            poll.poll_status = 'dismissed'
            poll.admin_action_note = reason
            poll.resolved_by = request.user
            poll.resolved_at = timezone.now()
            poll.save()
            print(f"NOTIFY TENANT ({poll.raised_by.username}): Poll '{poll.complaint_title}' was dismissed. Reason: {reason}")
            messages.success(request, "Poll dismissed.")
            
        elif action == 'escalate':
            poll.admin_action_note = "Escalated for Owner Review."
            poll.save()
            print(f"NOTIFY OWNER: Poll '{poll.complaint_title}' escalated internally.")
            messages.success(request, "Poll escalated internally.")
            
        return redirect('manage_complaints')

    active_polls = ComplaintPoll.objects.filter(poll_status='active').order_by('closes_at')
    
    from django.db.models import Case, When, IntegerField
    closed_polls = ComplaintPoll.objects.filter(poll_status='closed').annotate(
        priority_order=Case(
            When(priority_flag='high', then=1),
            When(priority_flag='medium', then=2),
            When(priority_flag='low', then=3),
            When(priority_flag='none', then=4),
            default=5,
            output_field=IntegerField(),
        )
    ).order_by('priority_order', '-closes_at')
    
    resolved_polls = ComplaintPoll.objects.filter(poll_status__in=['resolved', 'dismissed', 'withdrawn']).order_by('-resolved_at')

    return render(request, 'admin/manage_complaints.html', {
        'active_polls': active_polls,
        'closed_polls': closed_polls,
        'resolved_polls': resolved_polls
    })

@login_required
@admin_required
def manage_visitors(request):
    from datetime import date
    from django.utils import timezone
    if request.method == 'POST':
        action = request.POST.get('action')
        log_id = request.POST.get('log_id')
        log = get_object_or_404(VisitLog, id=log_id)
        if action == 'check_in':
            log.check_in_time = timezone.now()
            log.log_status = 'checked_in'
            log.save()
            messages.success(request, f"Visitor checked in successfully.")
        elif action == 'check_out':
            log.check_out_time = timezone.now()
            log.log_status = 'checked_out'
            log.save()
            messages.success(request, f"Visitor checked out successfully.")
        return redirect('manage_visitors')

    today = date.today()
    expected_today = VisitLog.objects.filter(visit_request__visit_date=today, log_status='expected')
    currently_in = VisitLog.objects.filter(log_status='checked_in')
    past_logs = VisitLog.objects.exclude(log_status__in=['expected', 'checked_in']).order_by('-id')[:50]

    return render(request, 'admin/manage_visitors.html', {
        'expected_today': expected_today,
        'currently_in': currently_in,
        'past_logs': past_logs
    })

@login_required
@parent_required
def parent_dashboard(request):
    if request.method == 'POST':
        vr = get_object_or_404(VisitRequest, id=request.POST.get('v_id'))
        
        # Verify parent owns this tenant
        if not hasattr(vr.tenant, 'tenant_profile') or vr.tenant.tenant_profile.parent != request.user:
            messages.error(request, "Unauthorized action.")
            return redirect('parent_dashboard')

        action = request.POST.get('action')
        if action == 'approve':
            vr.request_status = 'approved'
            vr.reviewed_by = request.user
            vr.save()
            VisitLog.objects.create(visit_request=vr, log_status='expected')
            messages.success(request, f"Visit request approved.")
        elif action == 'reject':
            vr.request_status = 'rejected'
            vr.rejection_reason = request.POST.get('reason', '')
            vr.reviewed_by = request.user
            vr.save()
            messages.success(request, f"Visit request rejected.")
        return redirect('parent_dashboard')

    children = request.user.children.all()
    tenants = [child.user for child in children]
    pending_visits = VisitRequest.objects.filter(tenant__in=tenants, request_status='pending').order_by('visit_date')
    history = VisitRequest.objects.filter(tenant__in=tenants).exclude(request_status='pending').order_by('-requested_at')[:20]

    return render(request, 'parent/parent_dashboard.html', {
        'pending_visits': pending_visits,
        'history': history,
        'children': children
    })

@login_required
def visitor_dashboard(request):
    if request.user.role != 'visitor':
        return redirect('login')
    
    # Handle VisitRequest creation
    if request.method == 'POST':
        from datetime import datetime
        try:
            v_date = datetime.strptime(request.POST.get('visit_date'), '%Y-%m-%d').date()
            if v_date <= datetime.now().date():
                messages.error(request, "Visit date must be in the future.")
            else:
                existing = VisitRequest.objects.filter(visitor=request.user.visitor_profile, visit_date=v_date).filter(request_status__in=['pending', 'approved']).exists()
                if existing:
                    messages.error(request, "You already have a pending or approved visit request for this date.")
                else:
                    VisitRequest.objects.create(
                        visitor=request.user.visitor_profile,
                        tenant=request.user.visitor_profile.tenant,
                        visit_date=v_date,
                        visit_time_slot=request.POST.get('time_slot'),
                        expected_duration=request.POST.get('duration'),
                        purpose=request.POST.get('purpose'),
                        number_of_accompanying_persons=request.POST.get('accompanying_persons', 0)
                    )
                    # Mock notification to Admin & Tenant
                    print(f"NOTIFY ADMIN: New Visit Request from {request.user.username} for tenant {request.user.visitor_profile.tenant.username}.")
                    print(f"NOTIFY TENANT: {request.user.username} wants to visit you on {v_date}.")
                    messages.success(request, "Visit request submitted successfully. Awaiting approval.")
        except Exception as e:
            messages.error(request, f"Error creating request: {str(e)}")
        return redirect('visitor_dashboard')
        
    my_requests = VisitRequest.objects.filter(visitor=request.user.visitor_profile).order_by('-requested_at')
    return render(request, 'visitor/visitor_dashboard.html', {'my_requests': my_requests})

@login_required
@admin_required
def manage_menu(request):
    from .models import WeeklyMenu
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if WeeklyMenu.objects.count() < 7:
        for day in days:
            WeeklyMenu.objects.get_or_create(day=day)
            
    if request.method == 'POST':
        for day in days:
            b = request.POST.get(f'breakfast_{day}')
            l = request.POST.get(f'lunch_{day}')
            d = request.POST.get(f'dinner_{day}')
            if b and l and d:
                menu = WeeklyMenu.objects.get(day=day)
                menu.breakfast = b
                menu.lunch = l
                menu.dinner = d
                menu.save()
        messages.success(request, "Weekly menu updated successfully!")
        return redirect('manage_menu')
    
    menus = WeeklyMenu.objects.all()
    day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    menus = sorted(menus, key=lambda x: day_order.get(x.day, 8))
    return render(request, 'admin/manage_menu.html', {'menus': menus})

@login_required
@admin_required
def manage_payments(request):
    from django.db.models import Sum
    from datetime import date
    if request.method == 'POST':
        t_id = request.POST.get('tenant_id')
        amount = request.POST.get('amount')
        if t_id and amount:
            try:
                tenant = User.objects.get(id=t_id, role='tenant')
                FeePayment.objects.create(
                    tenant=tenant, 
                    amount=amount, 
                    status='Paid', 
                    payment_method='Admin Record',
                    month=date.today()
                )
                messages.success(request, f"Payment of ₹{amount} noted for {tenant.username}.")
            except User.DoesNotExist:
                messages.error(request, "Invalid tenant selected.")
        return redirect('manage_payments')
        
    tenants = User.objects.filter(role='tenant', tenant_profile__room__isnull=False)
    payment_data = []
    
    for t in tenants:
        room_fee = t.tenant_profile.room.fee_per_month
        paid_this_month = FeePayment.objects.filter(
            tenant=t, 
            status='Paid',
            month__year=date.today().year,
            month__month=date.today().month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        due = room_fee - paid_this_month
        payment_data.append({
            'tenant': t,
            'room': t.tenant_profile.room,
            'fee': room_fee,
            'paid': paid_this_month,
            'due': due if due > 0 else 0,
            'status': 'Paid' if due <= 0 else 'Pending'
        })
        
    history = FeePayment.objects.all().order_by('-month')[:50]
    return render(request, 'admin/manage_payments.html', {'payment_data': payment_data, 'history': history})

# --- Tenant Dash & Features ---
@login_required
@tenant_required
def tenant_dashboard(request):
    evaluate_active_polls()

    # Withdrawal Action
    if request.method == 'POST' and 'withdraw_poll' in request.POST:
        poll_id = request.POST.get('poll_id')
        poll = get_object_or_404(ComplaintPoll, id=poll_id, raised_by=request.user)
        if (poll.vote_yes_count + poll.vote_no_count) == 0 and poll.poll_status == 'active':
            poll.poll_status = 'withdrawn'
            poll.save()
            messages.success(request, "Poll withdrawn successfully.")
        else:
            messages.error(request, "This poll cannot be withdrawn as votes have already been cast or it is closed.")
        return redirect('tenant_dashboard')

    # Voting Action
    if request.method == 'POST' and 'vote_action' in request.POST:
        poll_id = request.POST.get('poll_id')
        vote_choice = request.POST.get('vote_choice')
        poll = get_object_or_404(ComplaintPoll, id=poll_id, poll_status='active')
        
        if poll.raised_by == request.user:
            messages.error(request, "You cannot vote on your own complaint poll.")
            return redirect('tenant_dashboard')
            
        if PollVote.objects.filter(poll=poll, voter=request.user).exists():
            messages.error(request, "You have already voted on this poll.")
            return redirect('tenant_dashboard')
            
        PollVote.objects.create(poll=poll, voter=request.user, vote=vote_choice)
        if vote_choice == 'yes':
            poll.vote_yes_count += 1
        else:
            poll.vote_no_count += 1
        poll.save()
        messages.success(request, "Vote cast successfully.")
        return redirect('tenant_dashboard')

    profile, _ = TenantProfile.objects.get_or_create(user=request.user)
    my_polls = ComplaintPoll.objects.filter(raised_by=request.user).order_by('-raised_at')
    all_open_polls = ComplaintPoll.objects.filter(poll_status='active').exclude(raised_by=request.user).order_by('closes_at')
    voted_poll_ids = list(PollVote.objects.filter(voter=request.user).values_list('poll_id', flat=True))
    resolved_polls = ComplaintPoll.objects.filter(poll_status__in=['resolved', 'dismissed']).order_by('-resolved_at')[:20]

    return render(request, 'tenant/tenant_dashboard.html', {
        'profile': profile,
        'announcements': Announcement.objects.all().order_by('-date_posted')[:5],
        'my_polls': my_polls,
        'all_open_polls': all_open_polls,
        'voted_poll_ids': voted_poll_ids,
        'resolved_polls': resolved_polls
    })

@login_required
@tenant_required
def tenant_payments(request):
    from django.db.models import Sum
    from datetime import date
    profile = request.user.tenant_profile
    if not profile.room:
        messages.error(request, "You are not assigned a room yet.")
        return redirect('tenant_dashboard')
    
    room_fee = profile.room.fee_per_month
    paid_this_month = FeePayment.objects.filter(
        tenant=request.user, 
        status='Paid',
        month__year=date.today().year,
        month__month=date.today().month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    due = room_fee - paid_this_month
    due = due if due > 0 else 0

    history = FeePayment.objects.filter(tenant=request.user).order_by('-month')
    return render(request, 'tenant/tenant_payments.html', {
        'fee': room_fee, 
        'paid': paid_this_month,
        'due': due,
        'history': history
    })

@login_required
@tenant_required
def raise_complaint(request):
    evaluate_active_polls()
    
    if request.method == 'POST':
        active_count = ComplaintPoll.objects.filter(raised_by=request.user, poll_status='active').count()
        if active_count >= 3:
            messages.error(request, "You have reached the maximum of 3 active polls. Please wait for one to close.")
            return redirect('tenant_dashboard')

        title = request.POST.get('complaint_title')
        category = request.POST.get('complaint_category')
        
        ignore_warning = request.POST.get('ignore_warning')
        if not ignore_warning:
            similar = ComplaintPoll.objects.filter(complaint_category=category, poll_status='active', complaint_title__icontains=title).exists()
            if similar:
                return render(request, 'tenant/raise_complaint.html', {
                    'warning': "A similar active poll already exists. Do you still want to create a new one?",
                    'form_data': request.POST,
                    'poll_categories': ComplaintPoll.POLL_CATEGORY_CHOICES,
                    'duration_choices': ComplaintPoll.DURATION_CHOICES
                })

        duration = int(request.POST.get('poll_duration_days', 1))
        poll = ComplaintPoll.objects.create(
            raised_by=request.user,
            complaint_title=title,
            complaint_category=category,
            complaint_description=request.POST.get('complaint_description'),
            poll_question=request.POST.get('poll_question'),
            poll_duration_days=duration,
            closes_at=timezone.now() + timedelta(days=duration)
        )
        print(f"NOTIFY ACTIVE TENANTS: A new poll '{poll.complaint_title}' has been raised by {request.user.username}.")
        messages.success(request, "Complaint poll raised successfully.")
        return redirect('tenant_dashboard')
        
    return render(request, 'tenant/raise_complaint.html', {
        'poll_categories': ComplaintPoll.POLL_CATEGORY_CHOICES,
        'duration_choices': ComplaintPoll.DURATION_CHOICES
    })

@login_required
@tenant_required
def request_visitor(request):
    return render(request, 'tenant/request_visitor.html', {'my_visitors': []})

@login_required
@tenant_required
def view_menu(request):
    from .models import WeeklyMenu
    menus = WeeklyMenu.objects.all()
    day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    menus = sorted(menus, key=lambda x: day_order.get(x.day, 8))
    return render(request, 'tenant/view_menu.html', {'menus': menus})
