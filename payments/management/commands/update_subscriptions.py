from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from payments.models import Subscription

class Command(BaseCommand):
    help = "Update remaining days and status for active subscriptions, and send notifications"

    def handle(self, *args, **options):
        self.stdout.write("Running subscription update task...")
        today = timezone.now().date()
        active_subs = Subscription.objects.filter(status="Active")
        
        for sub in active_subs:
            if sub.lifetime:
                continue
                
            if not sub.end_date:
                continue
                
            end_date = sub.end_date.date() if hasattr(sub.end_date, 'date') else sub.end_date
            delta = end_date - today
            remaining = max(0, delta.days)
            
            sub.remaining_days = remaining
            
            if remaining <= 0:
                sub.status = "Expired"
                sub.save()
                self.stdout.write(f"Subscription for user {sub.user.email} has expired.")
                self.send_expiration_email(sub)
            else:
                sub.save()
                if remaining in [7, 3, 1]:
                    self.stdout.write(f"Sending {remaining}-day reminder to {sub.user.email}.")
                    self.send_reminder_email(sub, remaining)
                    
        self.stdout.write("Subscription update task completed successfully.")

    def send_reminder_email(self, sub, days):
        subject = f"Your RISE360 Institute MCQ Subscription expires in {days} days"
        message = (
            f"Hi {sub.user.get_full_name},\n\n"
            f"Your MCQ Subscription will expire in {days} days on {sub.end_date.strftime('%Y-%m-%d')}.\n"
            f"Please renew your subscription to continue practicing MCQs without interruption.\n\n"
            f"Best regards,\nRISE360 Institute Team"
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or "no-reply@rise360institute.com",
                [sub.user.email],
                fail_silently=True
            )
        except Exception as e:
            self.stderr.write(f"Failed to send email to {sub.user.email}: {e}")

    def send_expiration_email(self, sub):
        subject = "Your RISE360 Institute MCQ Subscription has expired"
        message = (
            f"Hi {sub.user.get_full_name},\n\n"
            f"Your MCQ Subscription has expired. You will no longer be able to access the MCQ practice and exam features.\n"
            f"Lectures and Books remain free for you. To restore MCQ access, please purchase a new plan.\n\n"
            f"Best regards,\nRISE360 Institute Team"
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or "no-reply@rise360institute.com",
                [sub.user.email],
                fail_silently=True
            )
        except Exception as e:
            self.stderr.write(f"Failed to send email to {sub.user.email}: {e}")
