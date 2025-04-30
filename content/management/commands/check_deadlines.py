from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from content.models import Task, Notification
from django.contrib.auth.models import User
from accounts.models import UserProfile
from datetime import timedelta

class Command(BaseCommand):
    help = 'Checks for upcoming deadlines and creates notifications'

    def handle(self, *args, **options):
        # Find tasks due within 48 hours
        deadline_threshold = timezone.now() + timedelta(hours=48)
        upcoming_tasks = Task.objects.filter(
            status='PENDING',
            due_date__lte=deadline_threshold,
            due_date__gt=timezone.now()
        )
        
        self.stdout.write(f"Found {upcoming_tasks.count()} tasks due within 48 hours")
        
        for task in upcoming_tasks:
            # Create notification if one doesn't already exist
            existing_notification = Notification.objects.filter(
                user=task.assignee,
                task=task,
                notification_type='DEADLINE',
                created_date__gt=timezone.now() - timedelta(hours=24)  # Don't create more than one per day
            ).exists()
            
            if not existing_notification:
                Notification.objects.create(
                    user=task.assignee,
                    task=task,
                    notification_type='DEADLINE',
                    message=f"Reminder: Task '{task.title}' is due on {task.due_date.strftime('%Y-%m-%d %H:%M')}"
                )
                self.stdout.write(self.style.SUCCESS(f"Created deadline notification for {task.assignee.username} - {task.title}"))
        
        # Find tasks due within 24 hours and notify XOs
        xo_threshold = timezone.now() + timedelta(hours=24)
        urgent_tasks = Task.objects.filter(
            status='PENDING',
            due_date__lte=xo_threshold,
            due_date__gt=timezone.now()
        )
        
        # Group tasks by platoon
        platoon_tasks = {}
        for task in urgent_tasks:
            if task.platoon not in platoon_tasks:
                platoon_tasks[task.platoon] = []
            platoon_tasks[task.platoon].append(task)
        
        # Notify XOs about tasks in their platoon
        for platoon, tasks in platoon_tasks.items():
            xo_profiles = UserProfile.objects.filter(role='XO', platoon=platoon)
            for profile in xo_profiles:
                for task in tasks:
                    existing_notification = Notification.objects.filter(
                        user=profile.user,
                        task=task,
                        notification_type='DEADLINE',
                        created_date__gt=timezone.now() - timedelta(hours=24)  # Don't create more than one per day
                    ).exists()
                    
                    if not existing_notification:
                        Notification.objects.create(
                            user=profile.user,
                            task=task,
                            notification_type='DEADLINE',
                            message=f"XO Alert: Task '{task.title}' for {task.assignee.username} is due within 24 hours"
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created XO alert for {profile.user.username} - {task.title}"))
        
        self.stdout.write(self.style.SUCCESS('Successfully checked deadlines and created notifications'))