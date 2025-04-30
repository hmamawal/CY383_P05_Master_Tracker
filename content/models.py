from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Challenge(models.Model):
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    participants = models.ManyToManyField(User, related_name='challenges_participated', blank=True)

    def __str__(self):
        return self.title

class Task(models.Model):
    # Status choices for tasks
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateTimeField()
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    platoon = models.CharField(max_length=20)
    
    class Meta:
        ordering = ['due_date']
        
    def __str__(self):
        return self.title
    
    def is_overdue(self):
        return self.due_date < timezone.now() and self.status == 'PENDING'
    
    @property
    def days_until_due(self):
        """Calculate days until (or since) due date"""
        delta = self.due_date.date() - timezone.now().date()
        return delta.days

class NCOR(models.Model):
    """Non-Compliance Report Model"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='ncors')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ncors')
    created_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="Failed to complete assigned task by the deadline.")
    
    def __str__(self):
        return f"NCOR: {self.user.username} - {self.task.title}"

class Notification(models.Model):
    """Notification Model for Task reminders"""
    NOTIFICATION_TYPES = [
        ('DEADLINE', 'Approaching Deadline'),
        ('OVERDUE', 'Task Overdue'),
        ('NEW_TASK', 'New Task Assigned'),
        ('COMPLETED', 'Task Completed'),
        ('NCOR', 'NCOR Generated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.notification_type}: {self.task.title}"