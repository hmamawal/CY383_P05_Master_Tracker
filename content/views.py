from django.shortcuts import render, redirect
from .models import Challenge
from .forms import ChallengeForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 

# Create your views here.
@login_required
def home(request):
    # retrieve all challenges
    challenges = Challenge.objects.all()
    # render the page with the information about the challenges
    return render(request, 'content/home.html', {'challenges': challenges})

@login_required
def add_challenge(request):
    # upon submission, retrieve and save the form data if it is valid. Then redirect to the home page.
    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    # otherwise, initialize the form and render the page to allow data entry
    else:
        form = ChallengeForm()
    return render(request, 'content/add_challenge.html', {'form': form})

@login_required
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)

    # Upon clicking the Join Challenge button, add the user to the participants of the challenge if the user is not already one.
    if request.method == 'POST' and request.user not in challenge.participants.all():
        challenge.participants.add(request.user)
        challenge.save()     

    return render(request, 'content/challenge_detail.html', {'challenge': challenge})