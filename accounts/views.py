from django.shortcuts import render, redirect
from .forms import RegistrationForm

# Create your views here.
def register(request):
    msg = None
    success = False
    form = RegistrationForm()
    if request.method == 'POST':
        # update the form
        form = RegistrationForm(request.POST)
        # save form data if valid
        if form.is_valid():
            # creates the user
            form.save()
            msg = 'Account created. Please <a href="login">Login</a>.'
            success = True
            return redirect('/accounts/login/')
        else:
            msg = 'Invalid input. Please review the information your provided and try again.'

    # store the form data in context so it can be passed to the page.    
    context = {'form':form, 'msg':msg, 'success':success}

    return render(request, 'registration/register.html', context)