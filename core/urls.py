from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/rooms/', views.manage_rooms, name='manage_rooms'),
    path('admin-dashboard/complaints/', views.manage_complaints, name='manage_complaints'),
    path('admin-dashboard/visitors/', views.manage_visitors, name='manage_visitors'),
    path('admin-dashboard/menu/', views.manage_menu, name='manage_menu'),
    path('admin-dashboard/payments/', views.manage_payments, name='manage_payments'),
    path('admin-dashboard/announcement/delete/<int:a_id>/', views.delete_announcement, name='delete_announcement'),

    # Tenant
    path('tenant-dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenant-dashboard/menu/', views.view_menu, name='view_menu'),
    path('tenant-dashboard/payments/', views.tenant_payments, name='tenant_payments'),
    path('tenant-dashboard/complaints/', views.raise_complaint, name='raise_complaint'),
    path('tenant-dashboard/visitors/', views.request_visitor, name='request_visitor'),
]
