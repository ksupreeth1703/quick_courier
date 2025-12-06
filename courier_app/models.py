from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser, Group, Permission

# class CustomUser(AbstractUser):
#     USER_TYPE_CHOICES = (
#         ('admin', 'Admin'),
#         ('delivery', 'Delivery Person'),
#         ('user', 'Normal User'),
#     )
    
#     user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
#     phone = models.CharField(max_length=15)
#     address = models.TextField()
#     is_verified = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # Add these to fix the reverse accessor clash
#     groups = models.ManyToManyField(
#         'auth.Group',
#         verbose_name='groups',
#         blank=True,
#         help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
#         related_name='custom_user_set',  # Changed
#         related_query_name='custom_user',
#     )
#     user_permissions = models.ManyToManyField(
#         'auth.Permission',
#         verbose_name='user permissions',
#         blank=True,
#         help_text='Specific permissions for this user.',
#         related_name='custom_user_set',  # Changed
#         related_query_name='custom_user',
#     )

#     def __str__(self):
#         return f"{self.username} ({self.get_user_type_display()})"

# class CustomUser(AbstractUser):
#     USER_TYPE_CHOICES = (
#         ('admin', 'Admin'),
#         ('delivery', 'Delivery Person'),
#         ('user', 'Normal User'),
#     )
    
#     user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
#     phone = models.CharField(max_length=15)
#     address = models.TextField()
#     is_verified = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # Specify unique related_name to avoid clash
#     groups = models.ManyToManyField(
#         Group,
#         verbose_name='groups',
#         blank=True,
#         help_text='The groups this user belongs to.',
#         related_name="customuser_set",
#         related_query_name="customuser",
#     )
#     user_permissions = models.ManyToManyField(
#         Permission,
#         verbose_name='user permissions',
#         blank=True,
#         help_text='Specific permissions for this user.',
#         related_name="customuser_set",
#         related_query_name="customuser",
#     )

#     def __str__(self):
#         return f"{self.username} ({self.get_user_type_display()})"



# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator

class CustomUser(AbstractUser):
    # Add your custom fields
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('delivery', 'Delivery Person'),
        ('user', 'Normal User'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    phone = models.CharField(max_length=15)
    address = models.TextField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Remove the custom groups and user_permissions fields
    # Let Django handle them automatically

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Parcel(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing Payment'),
        ('paid', 'Payment Confirmed'),
        ('assigned', 'Assigned to Delivery'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PARCEL_TYPE_CHOICES = (
        ('document', 'Document'),
        ('package', 'Package'),
        ('fragile', 'Fragile'),
        ('food', 'Food'),
        ('other', 'Other'),
    )
    
    tracking_number = models.CharField(max_length=20, unique=True)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_parcels')
    receiver_name = models.CharField(max_length=100)
    receiver_phone = models.CharField(max_length=15)
    receiver_address = models.TextField()
    
    parcel_type = models.CharField(max_length=20, choices=PARCEL_TYPE_CHOICES, default='package')
    weight = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    dimensions = models.CharField(max_length=50, help_text="LxWxH in cm")
    
    parcel_image = models.ImageField(upload_to='parcel_images/')
    description = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_man = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_parcels')
    
    pickup_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parcel #{self.tracking_number} - {self.sender.username} to {self.receiver_name}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash_on_delivery', 'Cash on Delivery'),
        ('online', 'Online Payment'),
        ('card', 'Credit/Debit Card'),
    )
    
    parcel = models.OneToOneField(Parcel, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Parcel #{self.parcel.tracking_number} - ${self.amount}"

class DeliveryUpdate(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name='updates')
    update_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    location = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)  # CHANGED FROM forms.TextField TO models.TextField
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Update for #{self.parcel.tracking_number}: {self.status}"