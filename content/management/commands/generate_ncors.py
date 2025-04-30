from django.core.management.base import BaseCommand
from django.utils import timezone
from content.models import Task, NCOR, Notification
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Generates NCORs for overdue tasks'

    def handle(self, *args, **options):
        # Find all overdue tasks
        overdue_tasks = Task.objects.filter(
            status='PENDING',
            due_date__lt=timezone.now()
        )
        
        self.stdout.write(f"Found {overdue_tasks.count()} overdue tasks")
        
        ncor_count = 0
        for task in overdue_tasks:
            # Check if NCOR already exists
            if not NCOR.objects.filter(task=task, user=task.assignee).exists():
                # Create NCOR
                ncor = NCOR.objects.create(
                    task=task,
                    user=task.assignee,
                    description=f"Failed to complete '{task.title}' by the deadline ({task.due_date.strftime('%Y-%m-%d %H:%M')})."
                )
                ncor_count += 1
                
                # Create notification for the cadet
                Notification.objects.create(
                    user=task.assignee,
                    task=task,
                    notification_type='NCOR',
                    message=f"An NCOR has been generated for your overdue task: {task.title}"
                )
                
                # Update task status
                task.status = 'OVERDUE'
                task.save()
                
                self.stdout.write(f"Generated NCOR for {task.assignee.username} - {task.title}")
                
                # Notify XOs
                xo_users = User.objects.filter(profile__role='XO', profile__platoon=task.platoon)
                for xo in xo_users:
                    Notification.objects.create(
                        user=xo,
                        task=task,
                        notification_type='NCOR',
                        message=f"NCOR generated for {task.assignee.username} - {task.title}"
                    )
        
        self.stdout.write(self.style.SUCCESS(f"Successfully generated {ncor_count} NCORs"))