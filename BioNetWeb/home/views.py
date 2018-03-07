from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.http import HttpResponse
from wsgiref.util import FileWrapper

from . import bnw_paths
from . import secret_login
from . import ssh_connection

import html
import time
import os
import io

# Create your views here.
def index(request):
    if request.method == 'POST':
        if 'submit_create' in request.POST:
            bngl_file = request.FILES.get('bngl', '')
            exp_file = request.FILES.get('exp', '')
            print(str(bngl_file))
            observables, bngl = get_free_parameters(bngl_file.file)
            exp = get_file_contents(exp_file.file)
            return render(request, 'config/create.html', {'observables': observables, 'bngl': bngl, 'exp': exp, 'bngl_name': str(bngl_file) , 'exp_name': str(exp_file)})

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
   file = ''
   for line in contents:
       file += line.decode('ascii')
       if "__FREE__" in line.decode('ascii'):
           out.append(line.decode('ascii').strip().split()[0])
   return out, file



def get_file_contents(contents):
    out = ''
    for line in contents:
        out += line.decode('ascii')
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
    if request.method == 'POST':
        conf = html.unescape(request.POST.get("conf"))
        bngl = html.unescape(request.POST.get("bngl"))
        exp = html.unescape(request.POST.get("exp"))
        bngl_name = html.unescape(request.POST.get("bnglName"))
        exp_name = html.unescape(request.POST.get("expName"))
        
        time_id = str(int(time.time()))
        user = str(request.user)
        # /scratch/jng86/bnw/[user]/[unique_time_id]
        location = os.path.join(bnw_paths.Paths.output, user, time_id).replace("\\", "/")
        bngl_loc = os.path.join(location, bngl_name).replace("\\", "/")
        exp_loc = os.path.join(location, exp_name).replace("\\", "/")
        conf_loc = os.path.join(location, time_id + ".conf").replace("\\", "/")
        job_name = "{}_{}".format(user, time_id)

        user_loc = os.path.join(bnw_paths.Paths.output, user).replace("\\", "/")
        
        conf = modify_conf(conf, time_id, location, bngl_loc, exp_loc, job_name)

        # TODO walltime, ntasks
        sbatch = bnw_paths.Paths.make_sbatch(job_name, location, time_id, "12:00:00", "5", conf_loc)

        sbatch_loc = os.path.join(location, time_id + ".sh").replace("\\", "/")

        # Establish SSH connection
        ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)

        # Check if user's directory exists
        stdin, stdout, stderr = ssh.execute("pwd")
        stdin, stdout, stderr = ssh.execute("[ ! -d {} ] && echo 'DNE'".format(user_loc))

        # User's directory does not exist -- create it
        if stdout:
            stdin, stdout, stderr = ssh.execute("mkdir {}".format(user_loc))

        
        # Make time_id directory
        stdin, stdout, stderr = ssh.execute("mkdir {}".format(location))

        sftp = ssh.ssh.open_sftp()        
        sftp.putfo(io.StringIO(conf), conf_loc)
        sftp.putfo(io.StringIO(bngl), bngl_loc)
        sftp.putfo(io.StringIO(exp), exp_loc)
        sftp.putfo(io.StringIO(sbatch), sbatch_loc)

        stdin, stdout, stderr = ssh.execute("sbatch {}".format(sbatch_loc))


        job_id = stdout[0].split()[-1]
        

        ssh.__del__()
        
    return render(request, 'home/user.html')


def modify_conf(conf, time_id, location, bngl_loc, exp_loc, job_name):
    
    overwrite_options = {"cluster_command": "", "cluster_software": "BNF2mpi", "pe_name": "", "queue_name": "",
                         "account_name": "", "job_sleep": "", "multisim": "", "use_cluster": "1", "save_cluster_output": "",
                         "run_job_from_worknode": "", "delete_old_files": "0", "make_plots": "", "verbosity": "",
                         "ask_create": "0", "ask_overwrite": "0", "show_welcome_message": "0",
                         "model": bngl_loc, "exp_file": exp_loc, "output_dir": location, "bng_command": bnw_paths.Paths.bng_command,
                         "job_name": job_name}

    lines = conf.split("\n")
    out = []
    ## Very inefficient
    for line in lines:
        overwrite = False
        for key in overwrite_options:
            if key in line:
                overwrite = True
                if overwrite_options[key]:
                    out.append("{}={}".format(key, overwrite_options[key]))
        if not overwrite:
            out.append(line)

    for key in overwrite_options:
        for line in out:
            if key in line:
                break
        if overwrite_options[key]:
            out.append("{}={}".format(key, overwrite_options[key]))
        
        

    return "\n".join(out)

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
