from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Challenge, Task, NCOR, Notification
from .forms import ChallengeForm, TaskForm, TaskCompletionForm
from accounts.models import UserProfile
from datetime import timedelta

# Updated home view to show Master Tracker dashboard instead of challenges
@login_required
def home(request):
    """Redirect to task dashboard as the main app interface"""
    return redirect('task_dashboard')

@login_required
def add_challenge(request):
    """Redirect to task dashboard instead of challenge creation"""
    return redirect('task_dashboard')

@login_required
def challenge_detail(request, challenge_id):
    """Redirect to task dashboard instead of showing challenge details"""
    return redirect('task_dashboard')

# Task related views
@login_required
def task_dashboard(request):
    """Main dashboard showing tasks based on user role"""
    user = request.user
    profile = UserProfile.objects.get(user=user)
    now = timezone.now()
    
    if profile.is_xo or profile.is_admin:
        # XOs see ALL tasks for ALL cadets, not just their platoon
        # Remove the platoon filter to see all tasks
        tasks_pending = Task.objects.filter(status='PENDING')
        tasks_completed = Task.objects.filter(status='COMPLETED')
        
        # Find overdue tasks - those with due date in the past but still pending
        tasks_overdue = Task.objects.filter(
            status='PENDING',
            due_date__lt=now
        )
        
        context = {
            'tasks_pending': tasks_pending,
            'tasks_completed': tasks_completed,
            'tasks_overdue': tasks_overdue,
            'is_xo': True,
        }
    else:
        # Cadets see only their tasks
        tasks_pending = Task.objects.filter(assignee=user, status='PENDING')
        tasks_completed = Task.objects.filter(assignee=user, status='COMPLETED')
        
        context = {
            'tasks_pending': tasks_pending,
            'tasks_completed': tasks_completed,
            'is_xo': False,
        }
    
    # Get unread notifications for the user
    notifications = Notification.objects.filter(user=user, read=False)
    context['notifications'] = notifications
    
    return render(request, 'content/task_dashboard.html', context)

@login_required
def task_detail(request, task_id):
    """View task details and allow completion"""
    task = get_object_or_404(Task, pk=task_id)
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    # Check if user is authorized to view this task
    if task.assignee != user and not profile.is_xo and profile.platoon != task.platoon:
        return HttpResponseForbidden("You do not have permission to view this task.")
    
    if request.method == 'POST' and task.assignee == user:
        form = TaskCompletionForm(request.POST, instance=task)
        if form.is_valid() and form.cleaned_data['confirmation']:
            task.status = 'COMPLETED'
            task.save()
            
            # Create a completion notification for the XO
            xo_users = User.objects.filter(profile__role='XO', profile__platoon=task.platoon)
            for xo in xo_users:
                Notification.objects.create(
                    user=xo,
                    task=task,
                    notification_type='COMPLETED',
                    message=f"Task '{task.title}' has been completed by {user.username}."
                )
                
            messages.success(request, "Task marked as completed successfully!")
            return redirect('task_dashboard')
    else:
        form = TaskCompletionForm()
    
    return render(request, 'content/task_detail.html', {
        'task': task,
        'form': form,
        'is_assignee': task.assignee == user,
        'is_xo': profile.is_xo,
    })

@login_required
def create_task(request):
    """Allow XOs to create new tasks"""
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    if not profile.is_xo and not profile.is_admin:
        return HttpResponseForbidden("Only Executive Officers can create tasks.")
    
    if request.method == 'POST':
        # Check if this is just to populate assignees list
        if 'populate_assignees' in request.POST:
            form = TaskForm(request.POST, creator=user)
            # Return to the form with the updated assignees list
            return render(request, 'content/create_task.html', {
                'form': form
            })
        
        # Otherwise process the actual task creation
        form = TaskForm(request.POST, creator=user)
        if form.is_valid():
            # Get data from the form but don't save yet
            task_title = form.cleaned_data.get('title')
            task_description = form.cleaned_data.get('description')
            task_due_date = form.cleaned_data.get('due_date')
            task_platoon = form.cleaned_data.get('platoon')
            assignees = form.cleaned_data.get('assignees')
            
            if not assignees or len(assignees) == 0:
                messages.error(request, "You must select at least one cadet to assign this task to.")
                return render(request, 'content/create_task.html', {'form': form})
            
            # Create task instances directly for each assignee
            assignment_count = 0
            for assignee in assignees:
                task_instance = Task.objects.create(
                    title=task_title,
                    description=task_description,
                    due_date=task_due_date,
                    created_date=timezone.now(),
                    status='PENDING',
                    assignee=assignee,  # Set the assignee here
                    creator=user,
                    platoon=task_platoon
                )
                assignment_count += 1
                
                # Create notification for each assignee
                Notification.objects.create(
                    user=assignee,
                    task=task_instance,
                    notification_type='NEW_TASK',
                    message=f"You have been assigned a new task: {task_title}"
                )
            
            messages.success(request, f"Task '{task_title}' created and assigned to {assignment_count} cadet(s).")
            return redirect('task_dashboard')
        else:
            # Form has validation errors, they will be displayed in the template
            pass
    else:
        form = TaskForm(creator=user, initial={'platoon': profile.platoon})
    
    return render(request, 'content/create_task.html', {
        'form': form
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def generate_ncors(request):
    """Generate NCORs for overdue tasks - should be called by a scheduler"""
    # Only XOs and admins can manually trigger NCOR generation
    if not request.user.profile.is_xo and not request.user.profile.is_admin:
        return HttpResponseForbidden("Only XOs and admins can generate NCORs.")
        
    # Find all overdue tasks
    overdue_tasks = Task.objects.filter(
        status='PENDING',
        due_date__lt=timezone.now()
    )
    
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
    
    messages.success(request, f"Generated {ncor_count} NCORs for overdue tasks.")
    return redirect('task_dashboard')

def check_upcoming_deadlines():
    """
    Function to check for upcoming deadlines and send notifications
    This should be called by a scheduler/cron job
    """
    # Find tasks due within 48 hours
    deadline_threshold = timezone.now() + timedelta(hours=48)
    upcoming_tasks = Task.objects.filter(
        status='PENDING',
        due_date__lte=deadline_threshold,
        due_date__gt=timezone.now()
    )
    
    for task in upcoming_tasks:
        # Create notification if one doesn't already exist
        existing_notification = Notification.objects.filter(
            user=task.assignee,
            task=task,
            notification_type='DEADLINE'
        ).exists()
        
        if not existing_notification:
            Notification.objects.create(
                user=task.assignee,
                task=task,
                notification_type='DEADLINE',
                message=f"Reminder: Task '{task.title}' is due on {task.due_date.strftime('%Y-%m-%d %H:%M')}"
            )
    
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
                    notification_type='DEADLINE'
                ).exists()
                
                if not existing_notification:
                    Notification.objects.create(
                        user=profile.user,
                        task=task,
                        notification_type='DEADLINE',
                        message=f"XO Alert: Task '{task.title}' for {task.assignee.username} is due within 24 hours"
                    )

@login_required
def compliance_dashboard(request):
    if not request.user.profile.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page")
    
    # Path to the latest compliance report
    import os
    import glob
    
    results_dir = os.path.join(settings.BASE_DIR, "compliance_results")
    report_files = glob.glob(os.path.join(results_dir, "compliance_summary_*.html"))
    
    if not report_files:
        return render(request, 'compliance/no_reports.html')
    
    # Get the latest report
    latest_report = max(report_files, key=os.path.getctime)
    
    with open(latest_report, 'r') as f:
        report_content = f.read()
    
    context = {
        'report_content': report_content,
        'report_date': datetime.fromtimestamp(os.path.getctime(latest_report)).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return render(request, 'compliance/dashboard.html', context)