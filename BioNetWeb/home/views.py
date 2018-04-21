from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from pymongo import MongoClient
from django.http import HttpResponse
from wsgiref.util import FileWrapper

from . import options
from . import bnw_paths
from . import secret_login
from . import ssh_connection

import html
import time
import json
import os
import io

def index(request):
    if request.method == 'POST':
        if 'submit_create' in request.POST:
            bngl_file = request.FILES.get('bngl', '')
            exp_file = request.FILES.get('exp', '')
            if not bngl_file:
                return HttpResponse()
            observables, bngl = get_free_parameters(bngl_file.file)

            if exp_file:
                exp = get_file_contents(exp_file.file)
            else:
                exp = ''

            return render(request, 'config/create.html', {'observables': observables,
                                                          'bngl': bngl,
                                                          'exp': exp,
                                                          'bngl_name': str(bngl_file),
                                                          'exp_name': str(exp_file),
                                                          'general_visible': options.general_visible,
                                                          'general_hidden': options.general_hidden,
                                                          'fitting_visible': options.fitting_visible,
                                                          'fitting_hidden': options.fitting_hidden,
                                                          'cluster_hidden': options.cluster_hidden,
                                                          'path_hidden': options.path_hidden,
                                                          'display_hidden': options.display_hidden})


    return render(request, 'home/index.html')


def add_user(username):
    username = to_mongo_key(username)
    users = establish_db_connect()
    users.insert({'user': str(username),
             'projects': {}})
    

def add_project(username, project_name):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    key = "projects.{}".format(project_name)
    structure = {"slurm_id": None, "input_files": {}, "output_files": {}}
    users.update({'user': username}, {'$set': {key: structure}})

def get_projects(username):
    username = to_mongo_key(username)
    users = establish_db_connect()
    for user in users.find({"user": username}):
        return user.get("projects")

def add_input_file(username, project_name, file_name, contents):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    file_name = to_mongo_key(file_name)
    users = establish_db_connect()
    key = "projects.{}.{}.{}".format(project_name, "input_files", file_name)
    users.update({'user': username}, {'$set': {key: contents}})

def add_output_file(username, project_name, file_name, contents):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    file_name = to_mongo_key(file_name)
    users = establish_db_connect()
    key = "projects.{}.{}.{}".format(project_name, "output_files", file_name)
    users.update({'user': username}, {'$set': {key: contents}})


def get_file(username, project_name, path):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    path = list(map(lambda x: to_mongo_key(x), path))
    users = establish_db_connect()
    for user in users.find({"user": username}):
        current_level = user["projects"][project_name]
        for p in path:
            current_level = current_level[p]
        return current_level
    

def set_slurm_id(username, project_name, slurm_id):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    key = "projects.{}.{}".format(project_name, "slurm_id")
    structure = str(slurm_id)
    users.update({'user': username}, {'$set': {key: structure}})


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

def example(request):
    if request.method == 'POST':
        if request.POST.get('step', '') == 'create':
            return render(request, 'home/example_create.html')
        
    return render(request, 'home/example.html')

def to_mongo_key(filename):
    return filename.replace(".", bnw_paths.Paths.delimiter)


def from_mongo_key(filename):
    return filename.replace(bnw_paths.Paths.delimiter, ".")


def get_output_structure(user, project_id, output_dir):
    # output_dir should be /scratch/bionetfit/bnw/[username]/[project_id]/[username]_[project_id]/
    
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    stdin, stdout, stderr = ssh.execute("pwd")
    stdin, stdout, stderr = ssh.execute("find {} -name \* -type f".format(output_dir))
    ssh.__del__()

    irrelevant_idx = len(output_dir.split("/"))
    out = {}
    
    for file in stdout[1:]:
        relevant = file.strip().split("/")[irrelevant_idx:]
        relevant = list(map(lambda x: to_mongo_key(x), relevant))
        
        # Add file to structure
        if len(relevant) == 1:
            out[relevant[0]] = ""
        # Add directory and file to structure
        else:
            current_level = out
            for idx, item in enumerate(relevant):
                if idx == len(relevant)-1:
                    current_level[item] = ""
                else:
                    if item not in current_level:
                        current_level[item] = {}
                    current_level = current_level[item]
    return out


# DB method
def set_output_structure(username, project_name, structure):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    key = "projects.{}.{}".format(project_name, "output_files")
    users.update({'user': username}, {'$set': {key: structure}})


def get_file_from_monsoon(path, user_loc):

    if "output_files" in path:
        start_idx = path.index("output_files") + 1
    else:
        start_idx = 0

    path_to_file = "/" + os.path.join(*(user_loc.split("/") + path[start_idx:])).replace("\\", "/")

    # Establish SSH connection
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    sftp = ssh.ssh.open_sftp()
    try:
        contents = io.BytesIO()
        sftp.getfo(path_to_file, contents)
    except FileNotFoundError:
        ssh.__del__()
        return ""
    ssh.__del__()

    return contents.getvalue().decode('ascii')


def user(request):
    if request.method == 'POST':

        if not request.user.is_authenticated:
            return HttpResponse()

        if not request.user.groups.filter(name="monsoon").exists():
            return HttpResponse()

        if "type" in request.POST:

            # Get project contents
            if request.POST.get("type") == "project":
                time_id = request.POST["project"]
                user = str(request.user)
                projects = get_projects(user)
                
                input_files = projects[time_id]["input_files"]
                input_file_names = list(map(lambda x: from_mongo_key(x), input_files))

                if not projects[time_id]["output_files"]:
                    output_dir = os.path.join(bnw_paths.Paths.output, user, time_id, "{}_{}".format(user, time_id)).replace("\\", "/")
                    output_structure = get_output_structure(user, time_id, output_dir)
                    set_output_structure(user, time_id, output_structure)
                           
                return HttpResponse(json.dumps(projects[time_id]))

            # Get file contents
            elif request.POST.get("type") == "file":
                path = json.loads(request.POST.get("file"))
                username = str(request.user)
                project_name = request.POST.get("project")
                file_contents = get_file(username, project_name, path)

                # Output file -- get file from Monsoon
                if not file_contents:
                    user_loc = os.path.join(bnw_paths.Paths.output, username, project_name, "{}_{}".format(username, project_name)).replace("\\", "/")
                    file_contents = get_file_from_monsoon(path, user_loc)
                    add_output_file(username, project_name, path[-1], file_contents)
                
                return HttpResponse(json.dumps(file_contents))

                

        # User is running a job on Monsoon
        else:

            if not request.user.is_authenticated:
                return HttpResponse()

            if not request.user.groups.filter(name="monsoon").exists():
                return HttpResponse()
            
            # Use seconds past epoch for unique job name for now
            time_id = str(int(time.time()))
            
            conf = html.unescape(request.POST.get("conf"))
            bngl = html.unescape(request.POST.get("bngl"))
            exp = html.unescape(request.POST.get("exp"))
            conf_name = "{}.conf".format(time_id)
            bngl_name = html.unescape(request.POST.get("bnglName"))
            exp_name = html.unescape(request.POST.get("expName"))
            
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

            # Close SSH and SFTP connections
            ssh.__del__()

            # Add relevent data to MongoDB
            add_project(user, time_id)
            for filename, contents in zip(
                map(lambda x: x.replace(".", bnw_paths.Paths.delimiter),
                    [conf_name, bngl_name, exp_name]), [conf, bngl, exp]):
                add_input_file(user, time_id, filename, contents)
            set_slurm_id(user, time_id, job_id)

            return HttpResponse(json.dumps("success"))


    # User is viewing user page normally
    if request.user.is_authenticated:
        projects = get_projects(str(request.user))
        return render(request, 'home/user.html', {"projects": list(projects.keys())})

    # User is not logged in
    else:
        return render(request, 'home/user.html')


def get_input_file_name_by_ext(ext, username, project_name):
    users = establish_db_connect()
    for user in users.find({"user": to_mongo_key(username)}):
        project = user["projects"].get(to_mongo_key(project_name), "")
        if not project:
            return ""
        input_files = project["input_files"]
    out = ""
    for file in input_files:
        if file.endswith("{}{}".format(bnw_paths.Paths.delimiter, ext)):
            out = file
            break
    return out


def check_exists_monsoon(fullpath):
    bash_str = 'if [ -e {} ]; then echo "True"; else echo "False"; fi'.format(fullpath)
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    stdin, stdout, stderr = ssh.execute("pwd")
    stdin, stdout, stderr = ssh.execute(bash_str)
    result = stdout[1]
    ssh.__del__()

    if "True" in result:
        return True
    else:
        return False


def get_bestfit_data(gdat_path, exp_path, output_dir):

    bestfit = "{}/{}".format(output_dir, bnw_paths.Paths.bestfit_data)
    exp = "{}/{}".format(output_dir, bnw_paths.Paths.exp_data)
    obv = "{}/{}".format(output_dir, bnw_paths.Paths.obv_names)

    if not all([check_exists_monsoon(path) for path in [bestfit, exp, obv]]):

        ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
        stdin, stdout, stderr = ssh.execute("pwd")
        stdin, stdout, stderr = ssh.execute("module load anaconda/3.latest")
        stdin, stdout, stderr = ssh.execute("python {} {} {} {}".format(bnw_paths.Paths.bestfit_plot_script,
                                                                        gdat_path,
                                                                        exp_path,
                                                                        output_dir))
        if len(stderr) > 0:
            ssh.__del__()
            return ["", "", ""]


    else:
        ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
        
    #stdout.channel.recv_exit_status()
    sftp = ssh.ssh.open_sftp()
    try:
        best_csv = io.BytesIO()
        exp_csv = io.BytesIO()
        obv_names = io.BytesIO()
        sftp.getfo(bestfit, best_csv)
        sftp.getfo(exp, exp_csv)
        sftp.getfo(obv, obv_names)
    except FileNotFoundError:
        ssh.__del__()
        return ["", "", ""]

    tmp = [best_csv, exp_csv, obv_names]
    return [item.getvalue().decode("ascii") for item in tmp]


def bestfit_plot(request):

    username = str(request.user)
    project_name = str(request.GET.get("p", ""))

    if not project_name or project_name == "null":
        return render(request, "home/visualization_error.html", {"message": "The project you requested could not be located."})

    output_dir = os.path.join(bnw_paths.Paths.output, username, project_name, "{}_{}".format(username, project_name)).replace("\\", "/")

    bngl_name = get_input_file_name_by_ext("bngl", username, project_name)
    gdat_name = bngl_name.split(bnw_paths.Paths.delimiter)[0] + ".gdat"
    gdat_path = os.path.join(output_dir, gdat_name).replace("\\", "/")

    exp_name = get_input_file_name_by_ext("exp", username, project_name)
    exp_path = os.path.join(bnw_paths.Paths.output, username, project_name, from_mongo_key(exp_name)).replace("\\", "/")

    best_csv, exp_csv, obv_names = get_bestfit_data(gdat_path, exp_path, output_dir)

    if not all([best_csv, exp_csv, obv_names]):
        return render(request, "home/visualization_error.html", {"message": "The appropriate files could not be found in your BioNetFit project output folder."})
    
    obv_names = filter(lambda obv: obv, obv_names.split("\n"))

    return render(request, "home/bestfit_plot.html", {"best_data": best_csv, "exp_data": exp_csv, "observables": obv_names})



def get_generational_data(exp_path, output_dir):
    # Establish SSH connection

    bestfit = "{}/{}".format(output_dir, bnw_paths.Paths.bestfit_data)
    avg = "{}/{}".format(output_dir, bnw_paths.Paths.avg_data)
    exp = "{}/{}".format(output_dir, bnw_paths.Paths.exp_data)
    obv = "{}/{}".format(output_dir, bnw_paths.Paths.obv_names)

    if not all([check_exists_monsoon(path) for path in [bestfit, avg, exp, obv]]):
        ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
        stdin, stdout, stderr = ssh.execute("pwd")
        stdin, stdout, stderr = ssh.execute("module load anaconda/3.latest")
        stdin, stdout, stderr = ssh.execute("python {} {} {}".format(bnw_paths.Paths.bestfit_plot_script,
                                                                     exp_path,
                                                                     output_dir))
        if len(stderr) > 0:
            ssh.__del__()
            return ["", "", "", ""]

    else:
        ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    
    #stdout.channel.recv_exit_status()
    sftp = ssh.ssh.open_sftp()
    try:
        best_csv = io.BytesIO()
        avg_csv = io.BytesIO()
        exp_csv = io.BytesIO()
        obv_names = io.BytesIO()
        sftp.getfo(bestfit, best_csv)
        sftp.getfo(avg, avg_csv)
        sftp.getfo(exp, exp_csv)
        sftp.getfo(obv, obv_names)
    except FileNotFoundError:
        ssh.__del__()
        return ["", "", "", ""]

    tmp = [best_csv, avg_data, exp_csv, obv_names]
    return [item.getvalue().decode("ascii") for item in tmp]


def generational_plot(request):

    username = str(request.user)
    project_name = str(request.GET.get("p", ""))

    if not project_name:
        return render(request, "home/visualization_error.html", {"message": "The project you requested could not be located."})

    output_dir = os.path.join(bnw_paths.Paths.output, username, project_name, "{}_{}".format(username, project_name)).replace("\\", "/")
    exp_name = get_input_file_name_by_ext("exp", username, project_name)
    exp_path = os.path.join(bnw_paths.Paths.output, username, project_name, from_mongo_key(exp_name)).replace("\\", "/")
    
    best_csv, avg_csv, exp_csv, obv_names = get_generational_data(exp_path, output_dir)

    if not all([best_csv, avg_csv, exp_csv, obv_names]):
        return render(request, "home/visualization_error.html", {"message": "The appropriate files could not be found in your BioNetFit project output folder."})
    
    obv_names = filter(lambda obv: obv, obv_names.split("\n"))
    num_gens = obv_names[-1]
    obv_names = obv_names[:-1]

    return render(request, "home/generational_plot.html", {"best_data": best_csv, "avg_data": avg_csv, "exp_data": exp_csv, "max_gen": num_gens, "observables": obv_names})
    

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


def establish_db_connect():

    client = MongoClient()
    db = client.BioNetFit
    users = db.users
    return users


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

            # Add user to MongoDB
            add_user(username)
            
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def get_project_archive(username, project_name):
    project_path = os.path.join(bnw_paths.Paths.output, username, project_name).replace("\\", "/")
    output = os.path.join(bnw_paths.Paths.output, username, "{}.zip".format(project_name))
    
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    stdin, stdout, stderr = ssh.execute("pwd")
    stdin, stdout, stderr = ssh.execute("zip {} -q -r {}".format(output, project_path))

    if len(stderr) > 0:
        ssh.__del__()
        return ""

    sftp = ssh.ssh.open_sftp()
    try:
        archive = io.BytesIO()
        sftp.getfo("{}.zip".format(project_path), archive)
    except FileNotFoundError:
        ssh.__del__()
        return ""

    stdin, stdout, stderr = ssh.execute("rm {}".format(output))
    ssh.__del__()

    return archive


def download_project(request):

    username = str(request.user)
    project_name = str(request.GET.get("p", ""))
    
    if not project_name or project_name == "null":
        return HttpResponse()
    
    archive_obj = get_project_archive(username, project_name)

    if not archive_obj:
        return HttpResponse()

    resp = HttpResponse(archive_obj.getvalue(), content_type="application/x-zip-compressed")
    resp["Content-Disposition"] = "attachment; filename={}".format(project_name + ".zip")

    return resp
