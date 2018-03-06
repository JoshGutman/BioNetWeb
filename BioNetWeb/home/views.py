from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.http import HttpResponse
from wsgiref.util import FileWrapper


# Create your views here.
def index(request):
    if request.method == 'POST':
        print("1")
        if 'submit_create' in request.POST:
            print(request.POST)
            bnglFile = request.FILES.get('bngl', '')
            expFile = request.FILES.get('exp', '')
            print(type(bnglFile), bnglFile.file, type(expFile), expFile)
            observables = get_free_parameters(bnglFile.file)
            print(observables)
            return render(request, 'config/create.html', {'observables': observables, 'bnglFile': bnglFile, 'expFiles': expFile})
        elif 'download' in request.POST:
            print('1')
            response = HttpResponse(FileWrapper(bnglFile.getvalue(), expFile.getValue()), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=myfile.zip'
            return response
        elif 'monsoon' in request.POST:
            print('2') 
    return render(request, 'home/index.html')

def get_free_parameters(contents):
   out = []
   for line in contents:
       if "__FREE__" in line.decode('ascii'):
           out.append(line.decode('ascii').strip().split()[0])
   return out

def about(request):
    if request.user.is_authenticated:
        print(request.user.get_username())
    return render(request, 'home/about.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('nickname', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                request.session.set_expiry(86400)
    return render(request, 'home/login.html')

def feedback(request):
    return render(request, 'home/feedback.html')

def resources(request):
    return render(request, 'home/resources.html')

def user(request):
    return render(request, 'home/user.html')

#def admin(request):
   # return render(request, 'home/admin.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
