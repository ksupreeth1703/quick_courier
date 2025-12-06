from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
import random
import string
from datetime import datetime

from .models import CustomUser, Parcel, Payment, DeliveryUpdate
from .forms import (CustomUserCreationForm, UserUpdateForm, ParcelForm, 
                   ParcelUpdateForm, PaymentForm, DeliveryUpdateForm, 
                   CustomAuthenticationForm)

# Helper functions for user type checks
def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

def is_delivery_person(user):
    return user.is_authenticated and user.user_type == 'delivery'

def is_normal_user(user):
    return user.is_authenticated and user.user_type == 'user'

def generate_tracking_number():
    """Generate unique tracking number"""
    letters = string.ascii_uppercase
    numbers = string.digits
    return f"TRK{''.join(random.choice(letters) for _ in range(3))}{''.join(random.choice(numbers) for _ in range(6))}"

# Home page
def home(request):
    return render(request, 'courier_app/home.html')

# Registration view
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'courier_app/register.html', {'form': form})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'courier_app/login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

# Dashboard view
@login_required
def dashboard(request):
    context = {}
    
    if request.user.user_type == 'admin':
        total_parcels = Parcel.objects.count()
        total_users = CustomUser.objects.count()
        delivered_parcels = Parcel.objects.filter(status='delivered').count()
        pending_parcels = Parcel.objects.filter(status='pending').count()
        
        context.update({
            'total_parcels': total_parcels,
            'total_users': total_users,
            'delivered_parcels': delivered_parcels,
            'pending_parcels': pending_parcels,
            'parcels': Parcel.objects.all().order_by('-created_at')[:10],
            'users': CustomUser.objects.all().order_by('-date_joined')[:5],
        })
        
    elif request.user.user_type == 'delivery':
        assigned_parcels = Parcel.objects.filter(delivery_man=request.user).order_by('-created_at')
        available_parcels = Parcel.objects.filter(status='paid', delivery_man=None).order_by('-created_at')
        
        context.update({
            'assigned_parcels': assigned_parcels,
            'available_parcels': available_parcels,
        })
        
    else:  # Normal user
        sent_parcels = Parcel.objects.filter(sender=request.user).order_by('-created_at')
        
        # Check for parcels where user is receiver (by phone number)
        received_parcels = Parcel.objects.filter(receiver_phone=request.user.phone).order_by('-created_at')
        
        context.update({
            'sent_parcels': sent_parcels,
            'received_parcels': received_parcels,
        })
    
    return render(request, 'courier_app/dashboard.html', context)

# Parcel CRUD operations
# @login_required
# def create_parcel(request):
#     if request.method == 'POST':
#         form = ParcelForm(request.POST, request.FILES)
#         if form.is_valid():
#             parcel = form.save(commit=False)
#             parcel.sender = request.user
#             parcel.tracking_number = generate_tracking_number()
#             parcel.save()
#             upload_to_s3
#             # Create payment record
#             payment_amount = float(parcel.weight) * 5  # $5 per kg
#             Payment.objects.create(
#                 parcel=parcel,
#                 amount=payment_amount,
#                 payment_method='online',
#                 payment_status='pending'
#             )
            
#             # Create initial update
#             DeliveryUpdate.objects.create(
#                 parcel=parcel,
#                 update_by=request.user,
#                 status='Parcel created',
#                 notes='Parcel has been created and is awaiting payment'
#             )
            
#             messages.success(request, f'Parcel created successfully! Tracking Number: {parcel.tracking_number}')
#             return redirect('parcel_detail', pk=parcel.pk)
#     else:
#         form = ParcelForm()
#     return render(request, 'courier_app/parcel_form.html', {'form': form, 'title': 'Create New Parcel'})






#from courier_app.utils.s3_upload import upload_to_s3


def send_email_sns(subject, message,name, amount):
    SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:114224740138:cpp-sns-x24108863"
    
    full_message = f"""Payment details:\n
        Name: {name}\n
        Amount: {amount}\n
        Message: {message}\n
    """

    try:
        # Use the correct region (eu-west-2)
        sns_client = boto3.client("sns", region_name="us-east-1",)  
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=full_message,
            Subject=subject
        )
        
        print(response)
        print(f"Email sent successfully! Message ID: {response['MessageId']}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False



import requests
import json

def send_email_via_lambda(receiver, subject, message):
    url = "https://o7344em8d2.execute-api.us-east-1.amazonaws.com/default/cpp-lambda-x24108863"

    payload = {
        "email": receiver,
        "subject": subject,
        "message": message
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    return response.json()




import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def upload_to_s3(file_obj, file_name, folder="parcel_images"):
    """
    Uploads a file to S3 using IAM Role or environment credentials.
    No AWS credentials are passed manually.
    """
    # Automatically picks credentials from IAM Role or ~/.aws credentials
    s3 = boto3.client("s3")

    try:
        key = f"{folder}/{file_name}"

        s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket="cpp-s3-x24108863",
            Key=key,
            ExtraArgs={"ContentType": file_obj.content_type}
        )

        return True

    except (NoCredentialsError, ClientError) as e:
        print("S3 Upload Error:", e)
        return False




@login_required
def create_parcel(request):
    if request.method == 'POST':
        form = ParcelForm(request.POST, request.FILES)
        if form.is_valid():
            parcel = form.save(commit=False)
            parcel.sender = request.user
            parcel.tracking_number = generate_tracking_number()

            parcel.save()

            # Upload to S3 after saving locally
            image_file = request.FILES.get("parcel_image")
            if image_file:
                upload_success = upload_to_s3(
                    file_obj=image_file,
                    file_name=parcel.parcel_image.name
                )

                if not upload_success:
                    messages.error(request, "Image uploaded locally but failed to upload to S3.")

            payment_amount = float(parcel.weight) * 5
            Payment.objects.create(
                parcel=parcel,
                amount=payment_amount,
                payment_method='online',
                payment_status='pending'
            )

            DeliveryUpdate.objects.create(
                parcel=parcel,
                update_by=request.user,
                status='Parcel created',
                notes='Parcel has been created and is awaiting payment'
            )

            messages.success(request, f"Parcel created! Tracking Number: {parcel.tracking_number}")
            return redirect('parcel_detail', pk=parcel.pk)
    else:
        form = ParcelForm()

    return render(request, 'courier_app/parcel_form.html', {'form': form, 'title': 'Create New Parcel'})







@login_required
def parcel_list(request):
    if request.user.user_type == 'admin':
        parcels = Parcel.objects.all().order_by('-created_at')
    elif request.user.user_type == 'delivery':
        parcels = Parcel.objects.filter(
            Q(delivery_man=request.user) | Q(status='paid', delivery_man=None)
        ).order_by('-created_at')
    else:
        parcels = Parcel.objects.filter(sender=request.user).order_by('-created_at')
    
    return render(request, 'courier_app/parcel_list.html', {'parcels': parcels})

@login_required
def parcel_detail(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk)
    
    # Check permission
    if request.user.user_type != 'admin' and parcel.sender != request.user and parcel.delivery_man != request.user:
        messages.error(request, 'You do not have permission to view this parcel.')
        return redirect('dashboard')
    
    updates = parcel.updates.all().order_by('-created_at')
    
    if request.method == 'POST':
        if request.user.user_type in ['delivery', 'admin']:
            update_form = DeliveryUpdateForm(request.POST)
            if update_form.is_valid():
                update = update_form.save(commit=False)
                update.parcel = parcel
                update.update_by = request.user
                update.save()
                
                # Update parcel status if changed
                if update.status != parcel.status:
                    parcel.status = update.status.lower()
                    if update.status.lower() == 'delivered':
                        parcel.delivery_date = datetime.now()
                    elif update.status.lower() == 'picked_up':
                        parcel.pickup_date = datetime.now()
                    parcel.save()
                
                messages.success(request, 'Delivery update added successfully!')
                return redirect('parcel_detail', pk=pk)
        else:
            messages.error(request, 'Only delivery personnel can add updates.')
    
    else:
        update_form = DeliveryUpdateForm()
    
    return render(request, 'courier_app/parcel_detail.html', {
        'parcel': parcel,
        'updates': updates,
        'update_form': update_form,
    })

@login_required
def update_parcel(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk)
    
    # Check permission - only admin and sender can update
    if not (request.user.user_type == 'admin' or parcel.sender == request.user):
        messages.error(request, 'You do not have permission to update this parcel.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ParcelUpdateForm(request.POST, instance=parcel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parcel updated successfully!')
            return redirect('parcel_detail', pk=pk)
    else:
        form = ParcelUpdateForm(instance=parcel)
    
    return render(request, 'courier_app/parcel_form.html', {
        'form': form,
        'title': 'Update Parcel',
        'parcel': parcel,
    })

@login_required
def delete_parcel(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk)
    
    # Check permission - only admin and sender can delete
    if not (request.user.user_type == 'admin' or parcel.sender == request.user):
        messages.error(request, 'You do not have permission to delete this parcel.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        tracking_number = parcel.tracking_number
        parcel.delete()
        messages.success(request, f'Parcel {tracking_number} deleted successfully!')
        return redirect('parcel_list')
    
    return render(request, 'courier_app/parcel_confirm_delete.html', {'parcel': parcel})

# Payment views
@login_required
def make_payment(request, parcel_id):
    parcel = get_object_or_404(Parcel, pk=parcel_id, sender=request.user)
    
    # Check if payment already exists
    try:
        payment = parcel.payment
    except Payment.DoesNotExist:
        # Create payment if doesn't exist
        payment_amount = float(parcel.weight) * 5
        payment = Payment.objects.create(
            parcel=parcel,
            amount=payment_amount,
            payment_method='online',
            payment_status='pending'
        )
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.payment_status = 'completed'
            payment.payment_date = datetime.now()
            payment.transaction_id = f"TXN{''.join(random.choice(string.digits) for _ in range(10))}"
            payment.save()
            
            # Update parcel status
            parcel.status = 'paid'
            parcel.save()
            
            # Create delivery update
            DeliveryUpdate.objects.create(
                parcel=parcel,
                update_by=request.user,
                status='Payment Completed',
                notes=f'Payment of ${payment.amount} completed via {payment.get_payment_method_display()}'
            )
            
            sender_name = parcel.sender.get_full_name() or parcel.sender.username

            
            send_email_sns("Payment", "a payemnt has made on system",sender_name,payment.amount)
            
            messages.success(request, 'Payment completed successfully!')
            return redirect('parcel_detail', pk=parcel.pk)
    else:
        form = PaymentForm(instance=payment)
    
    return render(request, 'courier_app/payment.html', {
        'form': form,
        'parcel': parcel,
        'payment': payment,
    })

# @login_required
# def payment_list(request):
#     if request.user.user_type == 'admin':
#         payments = Payment.objects.all().order_by('-created_at')
#     else:
#         # Get payments for parcels sent by the user
#         parcels = Parcel.objects.filter(sender=request.user)
#         payments = Payment.objects.filter(parcel__in=parcels).order_by('-created_at')
    
#     return render(request, 'courier_app/payment_list.html', {'payments': payments})





from django.db.models import Sum, Count

@login_required
def payment_list(request):
    if request.user.user_type == 'admin':
        payments = Payment.objects.all().order_by('-created_at')
    else:
        parcels = Parcel.objects.filter(sender=request.user)
        payments = Payment.objects.filter(parcel__in=parcels).order_by('-created_at')
    
    # Filter completed payments
    completed_payments = payments.filter(payment_status='completed')
    
    # Aggregate completed payments
    totals = completed_payments.aggregate(
        completed_count=Count('id'),
        total_amount=Sum('amount')
    )
    
    return render(request, 'courier_app/payment_list.html', {
        'payments': payments,
        'completed_count': totals['completed_count'],
        'total_amount': totals['total_amount'] or 0
    })





from django.urls import path
from parcel_details_export import export_parcel_pdf
from django.apps import apps

def export_parcel_details(request, parcel_id):
    Parcel = apps.get_model("courier_app", "Parcel")
    return export_parcel_pdf(Parcel, parcel_id)


# Delivery man views
@login_required
@user_passes_test(is_delivery_person)
def accept_parcel(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk, status='paid', delivery_man=None)
    
    if request.method == 'POST':
        parcel.delivery_man = request.user
        parcel.status = 'assigned'
        parcel.save()
        
        # Create update
        DeliveryUpdate.objects.create(
            parcel=parcel,
            update_by=request.user,
            status='Assigned to Delivery',
            notes=f'Assigned to delivery person: {request.user.get_full_name()}'
        )
        
        messages.success(request, f'Parcel #{parcel.tracking_number} assigned to you!')
        return redirect('dashboard')
    
    return render(request, 'courier_app/accept_parcel.html', {'parcel': parcel})

@login_required
@user_passes_test(is_delivery_person)
def mark_picked_up(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk, delivery_man=request.user)
    
    if request.method == 'POST':
        parcel.status = 'picked_up'
        parcel.pickup_date = datetime.now()
        parcel.save()
        
        # Create update
        DeliveryUpdate.objects.create(
            parcel=parcel,
            update_by=request.user,
            status='Picked Up',
            notes='Parcel has been picked up from sender'
        )
        
        messages.success(request, 'Parcel marked as picked up!')
        return redirect('parcel_detail', pk=pk)
    
    return render(request, 'courier_app/mark_status.html', {
        'parcel': parcel,
        'action': 'pick_up',
        'title': 'Mark as Picked Up'
    })

@login_required
@user_passes_test(is_delivery_person)
def mark_delivered(request, pk):
    parcel = get_object_or_404(Parcel, pk=pk, delivery_man=request.user)
    
    if request.method == 'POST':
        parcel.status = 'delivered'
        parcel.delivery_date = datetime.now()
        parcel.save()
        
        # Create update
        DeliveryUpdate.objects.create(
            parcel=parcel,
            update_by=request.user,
            status='Delivered',
            notes='Parcel has been delivered to receiver'
        )
        
        messages.success(request, 'Parcel marked as delivered!')
        sender_email = parcel.sender.email
        send_email_via_lambda(sender_email, "Parcel Delivered", "Your Parcel is Delivered Successfully.")
        return redirect('parcel_detail', pk=pk)
    
    return render(request, 'courier_app/mark_status.html', {
        'parcel': parcel,
        'action': 'delivered',
        'title': 'Mark as Delivered'
    })

# Admin views
@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'courier_app/admin_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def admin_parcels(request):
    parcels = Parcel.objects.all().order_by('-created_at')
    return render(request, 'courier_app/admin_parcels.html', {'parcels': parcels})

@login_required
@user_passes_test(is_admin)
def admin_payments(request):
    payments = Payment.objects.all().order_by('-created_at')
    return render(request, 'courier_app/admin_payments.html', {'payments': payments})

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_parcels = Parcel.objects.count()
    total_users = CustomUser.objects.count()
    total_delivery = CustomUser.objects.filter(user_type='delivery').count()
    total_revenue = sum(p.amount for p in Payment.objects.filter(payment_status='completed'))
    
    # Status counts
    status_counts = {}
    for status_code, status_name in Parcel.STATUS_CHOICES:
        count = Parcel.objects.filter(status=status_code).count()
        status_counts[status_name] = count
    
    context = {
        'total_parcels': total_parcels,
        'total_users': total_users,
        'total_delivery': total_delivery,
        'total_revenue': total_revenue,
        'status_counts': status_counts,
        'recent_parcels': Parcel.objects.all().order_by('-created_at')[:10],
        'recent_payments': Payment.objects.filter(payment_status='completed').order_by('-payment_date')[:10],
    }
    
    return render(request, 'courier_app/admin_dashboard.html', context)

@login_required
def profile(request):
    # Get the logged-in user
    user = request.user  # This is a CustomUser instance
    
    # If you need to get a specific user by username
    # user = get_object_or_404(CustomUser, username='admin')  # This returns a CustomUser instance
    
    # Then use the user object in queries
    sent_parcels = Parcel.objects.filter(sender=user)  # user object, not string
    assigned_parcels = Parcel.objects.filter(delivery_man=user)  # user object, not string
    
    context = {
        'user': user,
        'sent_parcels': sent_parcels,
        'assigned_parcels': assigned_parcels,
    }
    
    return render(request, 'courier_app/profile.html', context)