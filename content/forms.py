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
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        # Get the creator from the view
        self.creator = kwargs.pop('creator', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        
        # If platoon is provided in POST data, filter users by that platoon
        if 'platoon' in self.data:
            try:
                platoon = self.data.get('platoon')
                # Get users with the specified platoon in their profile
                profiles = UserProfile.objects.filter(platoon=platoon, role='CADET')
                self.fields['assignees'].queryset = User.objects.filter(
                    profile__in=profiles
                )
            except (ValueError, TypeError):
                pass

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