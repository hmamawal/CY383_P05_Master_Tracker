from django import forms
from .models import Challenge, Task
from django.contrib.auth.models import User
from accounts.models import UserProfile

class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ['title', 'description', 'start_date', 'end_date']

class TaskForm(forms.ModelForm):
    """Form for creating tasks by XOs"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'platoon']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    # Dynamic field to select assignees based on platoon
    assignees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Start with all users, will be filtered in __init__
        widget=forms.CheckboxSelectMultiple,
        required=True  # Make this required to ensure tasks are assigned
    )
    
    def __init__(self, *args, **kwargs):
        # Get the creator from the view
        self.creator = kwargs.pop('creator', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        
        # If platoon is provided in initial data, filter users by that platoon
        if 'initial' in kwargs and 'platoon' in kwargs['initial']:
            try:
                platoon = kwargs['initial']['platoon']
                # Get users with the specified platoon in their profile
                profiles = UserProfile.objects.filter(platoon=platoon, role='CADET')
                self.fields['assignees'].queryset = User.objects.filter(
                    profile__in=profiles
                )
            except (ValueError, TypeError):
                pass
        
        # If platoon is provided in POST data, filter users by that platoon
        if args and args[0] and 'platoon' in args[0]:
            try:
                platoon = args[0].get('platoon')
                # Get users with the specified platoon in their profile
                profiles = UserProfile.objects.filter(platoon=platoon, role='CADET')
                self.fields['assignees'].queryset = User.objects.filter(
                    profile__in=profiles
                )
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        # Make sure at least one assignee is selected
        assignees = cleaned_data.get('assignees')
        if not assignees or len(assignees) == 0:
            raise forms.ValidationError("You must select at least one cadet to assign this task to.")
        return cleaned_data

class TaskCompletionForm(forms.ModelForm):
    """Form for cadets to mark tasks as completed"""
    class Meta:
        model = Task
        fields = ['status']
        widgets = {
            'status': forms.HiddenInput(attrs={'value': 'COMPLETED'}),
        }
        
    # Additional fields might be required for task completion verification
    confirmation = forms.BooleanField(
        label="I confirm that I have completed this task",
        required=True
    )