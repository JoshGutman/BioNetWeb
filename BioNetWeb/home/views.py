from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from pymongo import MongoClient



# Create your views here.
def index(request):
    if request.method == 'POST':
        bnglFile = request.POST.get('bngl', '')
        expFile = request.POST.get('exp', '')
        return render(request, 'file_upload', {'bnglfile': bnglfile, 'expfile': expfile})

    return render(request, 'home/index.html')

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

###### MONGO DB FUNCTIONALITY #####
# Note from Tanner: Hey, so I will label
# and implement a number of mongo db
# fucntionalities here.

# First we generate a mongo connection
# We access the db BioNetFit, and
# the collection users.
def establish_db_connect():

    client = MongoClient()
    db = client.BioNetFit
    users = db.users
    return users


# Lets Start by Adding the User to the
# MongoDB. This accesses the request from
# user(request) and strips the username.
def add_db_user(request):

    users = establish_db_connect()
    username = request.user.username

    new_user = {
        "user":username
    }
    users.insert(new_user)
    return new_user

# Lets also add 2 files to the db
# under the specific username
# Fucntion used only for testing
def add_files(request):

    users = establish_db_connect()
    username = request.user.username

    users.update({"user":username}, {'$set':{"file1":
                    "This is a test file, named"
                    " file1!"}})
    users.update({"user":username}, {'$set':{"file2":
                    "This is a test file, named"
                    " file2!"}})


# Now that we have this, lets pull those
# files out and print them to the console.
# Fucntion used for testing, can be modified
def display_and_download(request):

    users = establish_db_connect()
    username = request.user.username

    for user in users.find({"user": username}):
        for field in user:
            if field != "user" and field != "_id":
                # Print the name of the file
                print(field)
                # Print the file itself
                print(user[field])
                # Lets download the mongodb file
                with open(field, 'a') as file:
                    file.write(user[field])

# Well thats pretty sweet, but can
# we write from an existing file
# to the db? I don't see why not!
def file_insert(request, filename):

    users = establish_db_connect()
    username = request.user.username

    # Avoid This, just for testing
    f = open(filename)
    text = f.read()
    users.update({"user": username}, {'$set': {filename: text}})

### END DB TESTING FUNCTIONS ###

def admin(request):
    return render(request, 'home/admin.html')

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
