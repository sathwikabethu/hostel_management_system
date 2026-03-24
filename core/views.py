from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum
from .forms import TenantRegistrationForm
from django.contrib.auth.decorators import login_required
from .decorators import admin_required, tenant_required
from .models import User, Room, Complaint, Announcement, TenantProfile, FeePayment, Visitor

# Auth Views
def register_view(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful. Welcome!')
            return redirect('tenant_dashboard')
    else:
        form = TenantRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect('admin_dashboard' if user.is_admin or user.is_superuser else 'tenant_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def home_view(request):
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
        'tenants_count': User.objects.filter(is_tenant=True).count(),
        'rooms_count': Room.objects.count(),
        'complaints_count': Complaint.objects.filter(status='Open').count(),
        'revenue': revenue
    }
    recent_tenants = User.objects.filter(is_tenant=True).order_by('-date_joined')[:5]
    announcements = Announcement.objects.all().order_by('-date_posted')
    return render(request, 'admin/admin_dashboard.html', {
        'stats': stats, 
        'recent_tenants': recent_tenants,
        'announcements': announcements
    })

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
    unassigned_tenants = User.objects.filter(is_tenant=True, tenant_profile__room__isnull=True)

    return render(request, 'admin/manage_rooms.html', {
        'rooms': Room.objects.all(),
        'available_rooms': available_rooms,
        'unassigned_tenants': unassigned_tenants
    })

@login_required
@admin_required
def manage_complaints(request):
    if request.method == 'POST':
        c = get_object_or_404(Complaint, id=request.POST.get('c_id'))
        c.status = request.POST.get('status')
        c.save()
        messages.success(request, "Complaint updated.")
        return redirect('manage_complaints')
    return render(request, 'admin/manage_complaints.html', {'complaints': Complaint.objects.all().order_by('-date_posted')})

@login_required
@admin_required
def manage_visitors(request):
    if request.method == 'POST':
        v = get_object_or_404(Visitor, id=request.POST.get('v_id'))
        v.status = request.POST.get('status')
        v.save()
        messages.success(request, f"Visitor {v.status}.")
        return redirect('manage_visitors')
    return render(request, 'admin/manage_visitors.html', {'visitors': Visitor.objects.all().order_by('-visit_date')})

@login_required
@admin_required
def manage_menu(request):
    from .models import WeeklyMenu
    if request.method == 'POST':
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
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
                tenant = User.objects.get(id=t_id, is_tenant=True)
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
        
    tenants = User.objects.filter(is_tenant=True, tenant_profile__room__isnull=False)
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
    profile, _ = TenantProfile.objects.get_or_create(user=request.user)
    return render(request, 'tenant/tenant_dashboard.html', {
        'profile': profile,
        'announcements': Announcement.objects.all().order_by('-date_posted')[:5]
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
    if request.method == 'POST':
        Complaint.objects.create(tenant=request.user, title=request.POST.get('title'), description=request.POST.get('desc'))
        messages.success(request, "Complaint submitted.")
        return redirect('tenant_dashboard')
    return render(request, 'tenant/raise_complaint.html', {'my_complaints': Complaint.objects.filter(tenant=request.user).order_by('-date_posted')})

@login_required
@tenant_required
def request_visitor(request):
    if request.method == 'POST':
        Visitor.objects.create(tenant=request.user, visitor_name=request.POST.get('name'), purpose=request.POST.get('purpose'), visit_date=request.POST.get('date'))
        messages.success(request, "Visitor pass requested.")
        return redirect('tenant_dashboard')
    return render(request, 'tenant/request_visitor.html', {'my_visitors': Visitor.objects.filter(tenant=request.user).order_by('-visit_date')})

@login_required
@tenant_required
def view_menu(request):
    from .models import WeeklyMenu
    menus = WeeklyMenu.objects.all()
    day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    menus = sorted(menus, key=lambda x: day_order.get(x.day, 8))
    return render(request, 'tenant/view_menu.html', {'menus': menus})
