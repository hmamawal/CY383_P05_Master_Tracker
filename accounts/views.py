from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=request.user.profile, user=request.user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=request.user.profile, user=request.user)
    
    context = {
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile.html', context)