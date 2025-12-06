from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Parcel, Payment, DeliveryUpdate

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'phone', 'address'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

class DeliveryUpdateInline(admin.TabularInline):
    model = DeliveryUpdate
    extra = 1
    readonly_fields = ('created_at',)

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'sender', 'receiver_name', 'parcel_type', 'status', 'delivery_man', 'created_at')
    list_filter = ('status', 'parcel_type', 'created_at')
    search_fields = ('tracking_number', 'sender__username', 'receiver_name', 'receiver_phone')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')
    inlines = [DeliveryUpdateInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('tracking_number', 'sender', 'receiver_name', 'receiver_phone', 'receiver_address')
        }),
        ('Parcel Details', {
            'fields': ('parcel_type', 'weight', 'dimensions', 'parcel_image', 'description')
        }),
        ('Delivery Information', {
            'fields': ('status', 'delivery_man', 'pickup_date', 'delivery_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'parcel', 'amount', 'payment_method', 'payment_status', 'payment_date')
    list_filter = ('payment_status', 'payment_method', 'payment_date')
    search_fields = ('transaction_id', 'parcel__tracking_number')
    readonly_fields = ('created_at',)

@admin.register(DeliveryUpdate)
class DeliveryUpdateAdmin(admin.ModelAdmin):
    list_display = ('parcel', 'update_by', 'status', 'location', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('parcel__tracking_number', 'update_by__username')
    readonly_fields = ('created_at',)