from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Parcel, Payment, DeliveryUpdate

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 
                 'phone', 'address', 'user_type', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove admin from registration choices
        self.fields['user_type'].choices = [
            ('user', 'Normal User'),
            ('delivery', 'Delivery Person'),
        ]

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone', 'address']

class ParcelForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = ['receiver_name', 'receiver_phone', 'receiver_address',
                 'parcel_type', 'weight', 'dimensions', 'parcel_image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'receiver_address': forms.Textarea(attrs={'rows': 3}),
        }

class ParcelUpdateForm(forms.ModelForm):
    class Meta:
        model = Parcel
        fields = ['status', 'delivery_man']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show delivery persons in the dropdown
        self.fields['delivery_man'].queryset = CustomUser.objects.filter(user_type='delivery')

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.RadioSelect(choices=Payment.PAYMENT_METHOD_CHOICES)
        }

class DeliveryUpdateForm(forms.ModelForm):
    class Meta:
        model = DeliveryUpdate
        fields = ['status', 'location', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))