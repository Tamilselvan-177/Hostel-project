import csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
from .models import User, FeeStructure, FeePayment, Profile, Due, CompleteDue, Issue
from django.utils.html import format_html
from django.contrib.auth.models import Group
from django.contrib import admin
from django.core.mail import send_mail
from .models import Due
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html, mark_safe
from django.contrib import admin
class DueAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'due_amount', 'balance', 'due_date', 'paid_status')
    
    # Specify a custom template for the admin list page
    change_list_template = "admin/dues_change_list.html"

    def get_urls(self):
        """
        Add custom URL patterns for downloading the due list and sending reminders.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-all-reminders/',
                self.admin_site.admin_view(self.send_all_reminders),
                name="send_all_reminders",
            ),
            path(
                'download-due-list/',
                self.admin_site.admin_view(self.download_due_list),
                name="download_due_list",
            ),
        ]
        return custom_urls + urls

    def send_all_reminders(self, request):
        """
        Send reminder emails to all due students.
        """
        dues = Due.objects.all()
        count = 0
        for due in dues:
            user = due.student
            if user.email:
                subject = "Fee Due Reminder"
                message = (
                    f"Hello {user.first_name},\n\n"
                    f"This is a reminder that you have an outstanding due of ₹{due.due_amount} "
                    f"for Semester {due.semester.semester} due on {due.due_date}.\n\n"
                    "Please clear your dues as soon as possible.\n\n"
                    "Thank you."
                )
                send_mail(subject, message, "your-email@example.com", [user.email], fail_silently=False)
                count += 1

        self.message_user(request, f"Reminder emails sent to {count} students.", level=messages.SUCCESS)
        return redirect("..")

    def download_due_list(self, request):
        """
        Generate and download a CSV file containing the due student list.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="due_students.csv"'

        writer = csv.writer(response)
        writer.writerow(['Student Name', 'Semester', 'Due Amount', 'Balance', 'Due Date', 'Paid Status'])

        dues = Due.objects.all()
        for due in dues:
            writer.writerow([
                due.student.get_full_name(),
                due.semester.semester,
                due.due_amount,
                due.balance,
                due.due_date,
                'Paid' if due.paid_status else 'Not Paid'
            ])

        return response
class CompleteDueAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'semester', 
        'total_paid', 
        'payment_mode', 
        'transaction_id', 
        'date_completed', 
        'fee_payment_details'
    )
    readonly_fields = ('fee_payment_details',)

    def fee_payment_details(self, obj):
        # Use filter() instead of get() to retrieve all related FeePayment records.
        fee_payments = FeePayment.objects.filter(
            student=obj.student,
            semester=obj.semester.semester  # This compares the integer value from FeeStructure
        )
        if fee_payments.exists():
            details = []
            for fee in fee_payments:
                details.append(
                    format_html(
                        "<div style='margin-bottom: 10px;'>"
                        "<strong>Transaction ID:</strong> {}<br>"
                        "<strong>Amount Paid:</strong> ₹{}<br>"
                        "<strong>Payment Mode:</strong> {}<br>"
                        "<strong>Date Paid:</strong> {}"
                        "</div>",
                        fee.transaction_id,
                        fee.amount_paid,
                        fee.payment_mode,
                        fee.date_paid.strftime("%d/%m/%Y %H:%M")
                    )
                )
            # Join all the HTML blocks and mark the result as safe.
            return mark_safe("".join(details))
        else:
            return "No Fee Payment found for this user and semester."
    fee_payment_details.short_description = "Fee Payment Details"
admin.site.register(FeeStructure)
admin.site.register(FeePayment)
admin.site.register(Profile)
admin.site.register(Issue)
admin.site.register(Due,DueAdmin)
admin.site.register(CompleteDue, CompleteDueAdmin)
# Register your models here.