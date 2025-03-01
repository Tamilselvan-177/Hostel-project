from pyexpat.errors import messages
from django.shortcuts import render

# Create your views here.
from .models import FeePayment, FeeStructure, User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import FeePayment, FeeStructure, User
import pdfkit

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import FeePayment, FeeStructure, User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .forms import IssueForm


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth import get_user_model

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages


from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User  # Ensure User model is imported

def login_view(request):
    if request.method == 'POST':
        roll_no = request.POST.get('register_number')  # Get roll number from form
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=roll_no)  # Fetch user by roll number
        except User.DoesNotExist:
            messages.error(request, "Invalid Roll Number or Password")
            return render(request, 'main/login.html')

        # Authenticate using the username field (Django expects username or email)
        authenticated_user = authenticate(request, username=user.username, password=password)
        print(authenticated_user)
        if authenticated_user is not None:
            login(request, authenticated_user)  # Log in the user
            messages.success(request, f"Welcome {authenticated_user.first_name}")
            return redirect('home')  # Redirect to dashboard or homepage
        else:
            messages.error(request, "Invalid Roll Number or Password")

    return render(request, 'main/login.html')



# Path to wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Update this with the correct path
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


# Generate and download invoice
def generate_invoice(request, payment_id):
    payment = FeePayment.objects.get(id=payment_id)
    context = {
        'payment': payment,
    }

    html_content = render_to_string('main/invoice_template.html', context)
    pdf = pdfkit.from_string(html_content, False, configuration=config)

    # Set up the HTTP response to send the PDF as an attachment
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{payment.id}.pdf"'
    return response
import pdfkit
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
import pdfkit

path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Update this with the correct path
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


def generate_invoice(request, payment_id):
    # Get the payment object
    payment = FeePayment.objects.get(id=payment_id)

    # Prepare context for the PDF
    context = {
        'payment': payment,
    }

    # Render HTML content for the invoice
    html_content = render_to_string('main/invoice_template.html', context)
    pdf = pdfkit.from_string(html_content, False, configuration=config)

    # Generate the PDF from HTML content

    # Set up the HTTP response to send the PDF as an attachment
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{payment.id}.pdf"'
    return response

from django.contrib import messages
from django.utils.timezone import now
from .models import Due, FeePayment, CompleteDue, FeeStructure, Profile
from django.contrib import messages
from django.utils.timezone import now
from .models import Profile, Due, FeePayment, CompleteDue, FeeStructure
@login_required(login_url='/login_view/')
def payment_dashboard(request):
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        messages.error(request, "No profile found for your account. Please create your profile first.")
        return redirect('profile')
    
    due_payments = Due.objects.filter(student=user, paid_status=False).order_by('semester')
    payment_history = FeePayment.objects.filter(student=user).order_by('-date_paid')
    complete_dues = CompleteDue.objects.filter(student=user).order_by('-date_completed')

    if request.method == "POST":
        # Get the due record's primary key from the form
        mobile_number = request.POST.get('mobile_number', '').strip()
        email = request.POST.get('email_id', '').strip()

        if not mobile_number or not email:
            messages.error(request, "Mobile number and email ID are required.")
            return redirect('financial')
        print(mobile_number,email)
        due_id = request.POST.get('due_id')
        try:
            due = Due.objects.get(id=due_id, student=user)
        except Due.DoesNotExist:
            messages.error(request, "No due found for the selected record.")
            return redirect('financial')
        
        payment_option = request.POST.get('payment_option')
        fee_structure = FeeStructure.objects.filter(semester=due.semester_code).first()
        if not fee_structure:
            messages.error(request, "Fee structure not found.")
            return redirect('financial')

        if payment_option == "full":
            amount_to_pay = due.due_amount
            due.paid_status = True
            due.balance = 0
        elif payment_option == "split_1":
            amount_to_pay = fee_structure.split_amount_1
            due.balance -= amount_to_pay
            due.paid_status = due.balance <= 0
        elif payment_option == "split_2":
            amount_to_pay = fee_structure.split_amount_2
            due.balance -= amount_to_pay
            due.paid_status = due.balance <= 0
        else:
            messages.error(request, "Invalid payment option selected.")
            return redirect('financial')

        due.save()

        FeePayment.objects.create(
            student=user,
            semester=due.semester_code,  # You can also use due.semester.semester if that makes more sense
            amount_paid=amount_to_pay,
            transaction_id=f"PAY-{now().strftime('%Y%m%d%H%M%S')}",
            payment_mode="Online",
            date_paid=now()
        )

        if due.paid_status:
            due.delete()

        messages.success(request, f"Payment of ₹{amount_to_pay} was successful.")
        return redirect('financial')

    context = {
        'due_payments': due_payments,
        'payment_history': payment_history,
        'complete_dues': complete_dues,
    }
    return render(request, 'main/financial.html', context)


    

@login_required(login_url='/login_view/')
def home(request):
    user = request.user

    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None

    # Fetch dues for the logged-in student
    dues = Due.objects.filter(student=user)

    # Fetch fee payments for the logged-in student
    fee_payments = FeePayment.objects.filter(student=user)

    # Fetch completed dues
    completed_dues = CompleteDue.objects.filter(student=user)
    
    context = {
        "user": user,
        "profile": profile,
        "dues": dues,
        "fee_payments": fee_payments,
        "completed_dues": completed_dues,
    }

    return render(request, "main/home.html", context)
@login_required(login_url='/login/')
def profile(request):
    user = request.user
    # Get or create the Profile instance for the user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        # Using .get() prevents a MultiValueDictKeyError if the key is missing.
        uploaded_file = request.FILES.get('profile_picture', None)
        if uploaded_file:
            profile.profile_picture = uploaded_file
            profile.save()
            messages.success(request, "Profile picture updated successfully!")
        else:
            messages.error(request, "No file selected for upload!")
        # Redirect to avoid resubmission of the form on page refresh
        return redirect('profile')

    context = {
        "user": user,
        "profile": profile,
    }
    return render(request, "main/profile.html", context)
@login_required(login_url='/login/')
def raiseIssue(request):
    form = IssueForm()
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.user = request.user
            issue.save()
            messages.success(request, "Your issue has been submitted successfully!")  # ✅ Add success message
            form = IssueForm()  # ✅ Reset form after submission
    
    return render(request, 'main/raiseIssue.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login_view')



#Reset Password Codes
import random
import string
from django.contrib.sites.shortcuts import get_current_site
from .models import Profile
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from .forms import ForgotPasswordForm, ResetPasswordForms
def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']  # Use cleaned_data to access the validated email
            try:
                user = User.objects.get(email=email)
                # Send email to reset password
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk)) 
                domain = request.get_host()

                subject = "Reset Password Requested"
                message = render_to_string('main/reset_password_email.html', {
                    'domain': domain,
                    'token': token,
                    'uid': uid
                })
                send_mail(subject, message, 'noreply@example.com', [email])
                messages.success(request, 'Email has been sent successfully')
                print(domain)
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address')  # Extra safeguard (not strictly necessary)
        else:
            messages.error(request, 'Invalid form submission')  # Show this only if form is invalid

    return render(request, "main/forgot_password.html", {"form": form})


def reset_password(request, uidb64, token):
    if request.method == "POST":
        print("Post is enter")
        form = ResetPasswordForms(request.POST)
        print(form.errors)
        if form.is_valid():
            print("forms vaild")
            new_password = form.cleaned_data['new_password']
            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            if user is not None and default_token_generator.check_token(user, token):
                print("Token is valid")
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your Password has Been Reset Successfully.")
                return redirect('login_view')
            else:
                print("Invalid token or user")
                messages.error(request, "The password reset link is invalid.")
    else:
        form = ResetPasswordForms()  # Render the form for GET requests.

    return render(request, 'main/reset_password.html', {"form": form})



    #online payment

