from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Parcel CRUD
    path('parcels/', views.parcel_list, name='parcel_list'),
    path('parcels/new/', views.create_parcel, name='create_parcel'),
    path('parcels/<int:pk>/', views.parcel_detail, name='parcel_detail'),
    path('parcels/<int:pk>/update/', views.update_parcel, name='update_parcel'),
    path('parcels/<int:pk>/delete/', views.delete_parcel, name='delete_parcel'),
    
    # Payment
    path('parcels/<int:parcel_id>/payment/', views.make_payment, name='make_payment'),
    path('payments/', views.payment_list, name='payment_list'),
    
    # Delivery actions
    path('parcels/<int:pk>/accept/', views.accept_parcel, name='accept_parcel'),
    path('parcels/<int:pk>/pickup/', views.mark_picked_up, name='mark_picked_up'),
    path('parcels/<int:pk>/deliver/', views.mark_delivered, name='mark_delivered'),
    
    # Admin views
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/parcels/', views.admin_parcels, name='admin_parcels'),
    path('admin/payments/', views.admin_payments, name='admin_payments'),
    
    path('parcel/<int:parcel_id>/export-pdf/', views.export_parcel_details, name='export_parcel_details'),

]