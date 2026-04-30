from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('register-parent/', views.register_parent_view, name='register_parent'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('elevate-me/', views.elevate_me, name='elevate_me'),
    path('register/parent/', views.register_parent_view, name='register_parent'),
    path('register/visitor/', views.register_visitor_view, name='register_visitor'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('admin-dashboard/approve-visit/<int:v_id>/', views.approve_visit_request, name='approve_visit_request'),
    path('admin-dashboard/rooms/', views.manage_rooms, name='manage_rooms'),
    path('admin-dashboard/complaints/', views.manage_complaints, name='manage_complaints'),
    path('admin-dashboard/visitors/', views.manage_visitors, name='manage_visitors'),
    path('admin-dashboard/menu/', views.manage_menu, name='manage_menu'),
    path('admin-dashboard/payments/', views.manage_payments, name='manage_payments'),
    path('admin-dashboard/announcement/delete/<int:a_id>/', views.delete_announcement, name='delete_announcement'),

    # Tenant
    path('tenant-dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    
    # Parent
    path('parent-dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('visitor-dashboard/', views.visitor_dashboard, name='visitor_dashboard'),
    path('tenant-dashboard/menu/', views.view_menu, name='view_menu'),
    path('tenant-dashboard/payments/', views.tenant_payments, name='tenant_payments'),
    path('tenant-dashboard/complaints/', views.raise_complaint, name='raise_complaint'),
    path('tenant-dashboard/visitors/', views.request_visitor, name='request_visitor'),
]
