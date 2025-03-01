from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db.models import Sum
from datetime import timedelta, date
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db.models import Sum
from django.contrib.auth.models import User
import os
from django.core.exceptions import ValidationError


def profile_picture_upload_to(instance, filename):
    # Get the file extension (e.g., .png, .jpg)
    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    # Construct the file name using the user's username
    return f"profile_pictures/{instance.user.username}{ext}"
class FeeStructure(models.Model):
    semester = models.IntegerField(unique=True)  # Semester-based fee structure
    full_amount = models.DecimalField(max_digits=10, decimal_places=2)
    split_amount_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    split_amount_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    def clean(self):
        """Validation before saving to the database"""
        if self.split_amount_1 is not None and self.split_amount_2 is not None:
            if self.split_amount_1 == self.split_amount_2:
                raise ValidationError("Split amounts must be different.")
            if self.split_amount_1 + self.split_amount_2 != self.full_amount:
                raise ValidationError("The sum of split amounts must be equal to the full amount.")

    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Semester {self.semester} - ₹{self.full_amount}"
    def __str__(self):
        return f"Semester {self.semester} - ₹{self.full_amount}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    semester = models.ForeignKey('FeeStructure', on_delete=models.CASCADE, related_name="profiles")
    due_date = models.DateField(default=now)
    
    # New fields for room details and phone number
    hostel = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Hostel or Block details (e.g., Block A)"
    )
    room_number = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        help_text="Room number (e.g., 102)"
    )
    bed = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        help_text="Bed identifier (e.g., B)"
    )
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text="Phone number"
    )
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_to,
        blank=True,
        null=True,
        help_text="Upload your profile picture"
    )

    def __str__(self):
        return f'{self.user.first_name} - Semester {self.semester.semester}'

class Due(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dues')
    semester = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="dues")  # Linked to FeeStructure
    semester_code = models.IntegerField(default=1)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_split_payment = models.BooleanField(default=False)
    paid_status = models.BooleanField(default=False)
    due_date = models.DateField()  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.first_name} - Sem {self.semester.semester} - Due: ₹{self.due_amount} - Balance: ₹{self.balance} - Due Date: {self.due_date}"

class FeePayment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    semester = models.IntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_mode = models.CharField(max_length=50, choices=[('Online', 'Online'), ('Cash', 'Cash')])
    date_paid = models.DateTimeField(auto_now_add=True)
    invoice = models.FileField(upload_to='invoices/', blank=True, null=True)
    is_split_payment = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.first_name} - Sem {self.semester} - Paid: ₹{self.amount_paid} - {self.transaction_id}"

class Issue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
# ------------------- FUNCTION TO AUTO-GENERATE DUES -------------------
from django.db.models.signals import post_save
from django.dispatch import receiver
@receiver(post_save, sender=Profile)
def generate_due_on_profile_update(sender, instance, created, **kwargs):
    """ Automatically create/update dues when semester is updated, fetching amount from FeeStructure """
    due = Due.objects.filter(student=instance.user,semester=instance.semester).first()  # Fetch Due linked to Profile
    completed_due = CompleteDue.objects.filter(student=instance.user,semester=instance.semester).first()  # Fetch Due linked to Profile
    print(due,completed_due)
    if  due==None and  completed_due==None:
        
        fee_structure = instance.semester  # Fetch FeeStructure linked to Profile

        if fee_structure:
            # Delete old dues for this user before creating a new one

            total_due = fee_structure.full_amount
            due_date = instance.due_date  # Fetch due date from Profile

            # Create due and set balance equal to full amount
            Due.objects.create(
                student=instance.user,
                semester=fee_structure,
                due_amount=total_due,
                balance=total_due,  # Balance should be the full amount
                is_split_payment=False,  # Not considering split payments
                due_date=due_date,
                semester_code=fee_structure.semester
            )
class CompleteDue(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    semester = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)

    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=50, choices=[('Online', 'Online'), ('Cash', 'Cash')])
    transaction_id = models.CharField(max_length=100, unique=True)
    date_completed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.first_name} - Sem {self.semester} - Paid ₹{self.total_paid}"
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete,post_delete
from django.dispatch import receiver
from django.utils.timezone import now
@receiver(pre_delete, sender=Due)
def move_to_complete_due(sender, instance, **kwargs):

    """ Store fully paid due records in CompleteDue before deletion. """
    if instance.paid_status:  # Only store if fully paid

        CompleteDue.objects.create(
            student=instance.student,
            semester=instance.semester,
            total_paid=instance.due_amount,
            payment_mode="Online",
            transaction_id=f"PAY-{now().strftime('%Y%m%d%H%M%S')}",
            date_completed=now()
        )
