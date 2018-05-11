from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from pymongo import MongoClient
from django.core.mail import send_mail, mail_admins
from django.http import HttpResponse
from wsgiref.util import FileWrapper

from . import limits
from . import options
from . import bnw_paths
from . import polynomial
from . import secret_login
from . import ssh_connection
from . import forms

import zipfile
import pickle
import html
import time
import json
import os
import io

def index(request):
    if request.method == 'POST':
        if 'submit_create' in request.POST:
            if 'edit' in request.POST:
                project_id = request.POST.get('project', '')
                if not project_id:
                    return HttpResponse()
                username = str(request.user)

                bngl_file = get_file_name_by_ext(username, project_id, ['input_files'], 'bngl')
                exp_file = get_file_name_by_ext(username, project_id, ['input_files'], 'exp')

                bngl = get_file(username, project_id, ['input_files', bngl_file])
                exp = get_file(username, project_id, ['input_files', bngl_file])

                observables = get_free_parameters_str(bngl)

                conf_file = get_file_name_by_ext(username, project_id, ['input_files'], 'conf')
                conf = get_file(username, project_id, ['input_files', conf_file])

                option_fields = {}

                for line in conf.split('\n'):
                    if not line or line.startswith("#"):
                        continue
                    if '=' in line:
                        fields = line.split('=')
                        if fields[0] in option_fields:
                            option_fields[fields[0]].append(fields[1].strip())
                        else:
                            option_fields[fields[0]] = [fields[1].strip()]
                    else:
                        option_fields[line.strip()] = []

                for field in option_fields:
                    if field not in ["loguniform_var", "random_var", "lognormrandom_var", "static_list_var"]:
                        if len(option_fields[field]) > 1:
                            option_fields[field] = option_fields[field][:1]
                

            else:
                bngl_file = request.FILES.get('bngl', '')
                exp_file = request.FILES.get('exp', '')
                if not bngl_file:
                    return HttpResponse()
                observables, bngl = get_free_parameters(bngl_file.file)

                if exp_file:
                    exp = get_file_contents(exp_file.file)
                else:
                    exp = ''

                option_fields = {}


            warnings = []
            project_limit_reached = False
            if request.user.is_authenticated:
                #if not request.user.groups.filter(name="monsoon").exists():
                if not request.user.can_use_monsoon:
                    warnings.append("Your account is not approved -- you will not be able to run BioNetFit on Monsoon.")
                if get_num_projects(str(request.user)) >= limits.NUM_PROJECTS_LIMIT:
                    warnings.append("You have reached the maximum allowed number of projects -- you will not be able to run BioNetFit on Monsoon.")
                    project_limit_reached = True
            else:
                warnings.append("You are not logged in -- you will not be able to run BioNetFit on Monsoon.")
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
                                                          'display_hidden': options.display_hidden,
                                                          'memory_limit': limits.MEMORY_LIMIT,
                                                          'walltime_limit': limits.WALLTIME_LIMIT,
                                                          'name_length_limit': limits.NAME_LENGTH_LIMIT,
                                                          'parallel_count_limit': limits.PARALLEL_COUNT_LIMIT,
                                                          'warnings': warnings,
                                                          'project_limit_reached': project_limit_reached,
                                                          'option_fields': json.dumps(option_fields)})


    return render(request, 'home/index.html')


def add_user(username):
    initial_time = int(time.time()) - 600
    username = to_mongo_key(username)
    users = establish_db_connect()
    users.insert({'user': str(username),
                  'projects': {},
                  'last_check': initial_time,
                  'last_project': initial_time})
    

def add_project(username, project_name):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    key = "projects.{}".format(project_name)
    structure = {"status": None, "slurm_id": None, "input_files": {}, "output_files": {}}
    users.update({'user': username}, {'$set': {key: structure}})

def get_projects(username):
    username = to_mongo_key(username)
    users = establish_db_connect()
    for user in users.find({"user": username}):
        return user.get("projects")

def delete_project(username, project_id):
    slurm_id = get_slurm_id(username, project_id)

    # Delete project on MongoDB
    username_mongo = to_mongo_key(username)
    project_id_mongo = to_mongo_key(project_id)
    key = "projects.{}".format(project_id_mongo)
    users = establish_db_connect()
    users.update({'user': username_mongo}, {'$unset': {key: ''}})

    # Delete project on Monsoon
    project_dir = os.path.join(bnw_paths.Paths.output, username, project_id).replace("\\", "/")
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    stdin, stdout, stderr = ssh.execute("scancel {}".format(slurm_id))  # Cancel job
    stdin, stdout, stderr = ssh.execute("rm -r {}".format(project_dir)) # Delete project directory
    ssh.__del__()

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

def get_file_name_by_ext(username, project_name, path, ext):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    path = list(map(lambda x: to_mongo_key(x), path))
    users = establish_db_connect()
    for user in users.find({"user": username}):
        current_level = user["projects"][project_name]
        for p in path:
            current_level = current_level[p]
        for item in current_level:
            if item.endswith(ext):
                return item


def set_slurm_id(username, project_name, slurm_id):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    key = "projects.{}.{}".format(project_name, "slurm_id")
    structure = str(slurm_id)
    users.update({'user': username}, {'$set': {key: structure}})


def get_slurm_id(username, project_name):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    for user in users.find({"user": username}):
        return user["projects"][project_name]["slurm_id"]


def set_last_status_time(username):
    username = to_mongo_key(username)
    users = establish_db_connect()
    users.update({"user": username}, {"$set": {"last_check": int(time.time())}})


def get_last_status_time(username):
    username = to_mongo_key(username)
    users = establish_db_connect()
    for user in users.find({"user": username}):
        return user["last_check"]


def set_status(username, project_name, status):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    key = "projects.{}.{}".format(project_name, "status")
    users.update({'user': username}, {'$set': {key: str(status)}})


def get_status(username, project_name):
    username = to_mongo_key(username)
    project_name = to_mongo_key(project_name)
    users = establish_db_connect()
    for user in users.find({"user": username}):
        return user["projects"][project_name]["status"]


def get_num_projects(username):
    username = to_mongo_key(username)
    users = establish_db_connect()
    for user in users.find({"user": username}):
        return len(user["projects"])


def get_free_parameters(contents):
    out = []
    file = ''
    for line in contents:
        file += line.decode('ascii')
        if "__FREE__" in line.decode('ascii'):
            out.append(line.decode('ascii').strip().split()[0])
    return out, file


def get_free_parameters_str(contents):
    out = []
    for line in contents.split("\n"):
       if "__FREE__" in line:
           out.append(line.strip().split()[0])
    return out


def get_file_contents(contents):
    out = ''
    for line in contents:
        out += line.decode('ascii')
    return out



def about(request):
    return render(request, 'home/about.html')


'''
def login(request):
    if request.user.is_authenticated:
        return HttpRedirect("/")
    if request.method == 'POST':
        username = request.POST.get('nickname', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                request.session.set_expiry(86400)
    return render(request, 'home/login.html')
'''


def feedback(request):
    return render(request, 'home/feedback.html')

def thankyou(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        comments = request.POST.get('comments', '')
        message = 'Name: {}\nEmail: {}\n\nComments:\n{}\n'.format(
            name,
            email,
            comments)
        if all([name, email, comments]):
            mail_admins(
                'BioNetWeb Feedback Received',
                message,
                fail_silently=False
            )
    return render(request, 'home/thankyou.html')


def resources(request):
    return render(request, 'home/resources.html')


def example(request):
    if request.method == 'POST':
        if request.POST.get('step', '') == 'create':
            return render(request, 'home/example_create.html')
        elif request.POST.get('step', '') == 'view':
            return render(request, 'home/example_view.html', {"projects": ["polynomial"]})
        elif request.POST.get('type', '') == 'project':
            return HttpResponse(json.dumps(polynomial.polynomial))
        elif request.POST.get('type', '') == 'file':
            path = json.loads(request.POST.get('file', ''))
            current_level = polynomial.polynomial
            for p in path:
                current_level = current_level[p]
            return HttpResponse(json.dumps(current_level))        
            
    return render(request, 'home/example.html')

def example_download(request):
    archive = download_project_polynomial()
    resp = HttpResponse(archive.getvalue(), content_type="application/x-zip-compressed")
    resp["Content-Disposition"] = "attachment; filename={}".format("polynomial.zip")
    return resp

def example_bestfit(request):
    return render(request, "home/example_bestfit_plot.html", {"observables": ["x", "y"]})

def example_generation(request):
    return render(request, "home/example_generation_plot.html", {"observables": ["x", "y"], "max_gen": 100})

def example_fitvalue(request):
    return render(request, "home/example_fitvalue_plot.html", {"observables": ["x", "y"]})

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

        #if not request.user.groups.filter(name="monsoon").exists():
        if not request.user.can_use_monsoon:
            return HttpResponse()


        if "type" in request.POST:

            # Get project contents
            if request.POST.get("type") == "project":
                project_id = request.POST["project"]
                user = str(request.user)
                projects = get_projects(user)
                
                input_files = projects[project_id]["input_files"]
                input_file_names = list(map(lambda x: from_mongo_key(x), input_files))

                if not projects[project_id]["output_files"]:
                    output_dir = os.path.join(bnw_paths.Paths.output, user, project_id, "{}_{}".format(user, project_id)).replace("\\", "/")
                    output_structure = get_output_structure(user, project_id, output_dir)
                    set_output_structure(user, project_id, output_structure)

                return HttpResponse(json.dumps({"structure": projects[project_id], "status": get_status(user, project_id)}))

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


            # Get job status
            elif request.POST.get("type") == "status":
                project_name = request.POST.get("project")
                username = str(request.user)
                if int(time.time()) - get_last_status_time(username) < limits.STATUS_RATE_LIMIT:
                    return HttpResponse("")
                slurm_id = get_slurm_id(username, project_name)
                status = check_job_status(slurm_id)
                set_last_status_time(username)
                if status == get_status(username, project_name):
                    return HttpResponse(json.dumps(status))
                set_status(username, project_name, status)
                
                # Update files in MongoDB
                output_dir = os.path.join(bnw_paths.Paths.output, username, project_name, "{}_{}".format(username, project_name)).replace("\\", "/")
                output_structure = get_output_structure(username, project_name, output_dir)
                set_output_structure(username, project_name, output_structure)
                
                return HttpResponse(json.dumps(status))


            elif request.POST.get("type") == "delete":
                project_name = request.POST.get("project")
                username = str(request.user)
                delete_project(username, project_name)
                return HttpResponse(json.dumps("success"))

                

        # User is running a job on Monsoon
        else:

            if not request.user.is_authenticated:
                return HttpResponse()

            #if not request.user.groups.filter(name="monsoon").exists():
            if not request.user.can_use_monsoon:
                return HttpResponse()

            user = str(request.user)
            if get_num_projects(user) >= limits.NUM_PROJECTS_LIMIT:
                return HttpResponse()
            
            # Use seconds past epoch for unique job name if project name is not valid
            project_name = request.POST.get("projectName", "")
            if not project_name or not project_name_is_valid(project_name):
                project_id = str(int(time.time()))
            else:
                project_id = project_name

            # Get and check walltime
            walltime = request.POST.get("walltime", "")
            if not walltime or not walltime_is_valid(walltime):
                walltime = "01:00:00"
            
            # Get and check memory
            memory = request.POST.get("memory", "")
            if not memory or not memory_is_valid(memory):
                memory = "8000"
            else:
                memory = str(int(memory) * 1000)

            # Get and check parallel count
            parallel_count = request.POST.get("parallelCount", "")
            if not parallel_count or not parallel_count_is_valid:
                parallel_count = "2"
            
            conf = html.unescape(request.POST.get("conf"))
            bngl = html.unescape(request.POST.get("bngl"))
            exp = html.unescape(request.POST.get("exp"))
            conf_name = "{}.conf".format(project_id)
            bngl_name = html.unescape(request.POST.get("bnglName"))
            exp_name = html.unescape(request.POST.get("expName"))
            
            
            # /scratch/jng86/bnw/[user]/[unique_project_id]
            location = os.path.join(bnw_paths.Paths.output, user, project_id).replace("\\", "/")
            bngl_loc = os.path.join(location, bngl_name).replace("\\", "/")
            exp_loc = os.path.join(location, exp_name).replace("\\", "/")
            conf_loc = os.path.join(location, project_id + ".conf").replace("\\", "/")
            job_name = "{}_{}".format(user, project_id)

            user_loc = os.path.join(bnw_paths.Paths.output, user).replace("\\", "/")
            
            conf = modify_conf(conf, project_id, location, bngl_loc, exp_loc, job_name)

            # Create .sh file
            sbatch = bnw_paths.Paths.make_sbatch(job_name, location, project_id, walltime, memory, int(parallel_count)+1, conf_loc, exp_loc, os.path.join(location, job_name, bngl_name.replace("bngl", "gdat")).replace("\\", "/"))
            sbatch_loc = os.path.join(location, project_id + ".sh").replace("\\", "/")

            # Establish SSH connection
            ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)

            # Check if user's directory exists
            stdin, stdout, stderr = ssh.execute("pwd")
            stdin, stdout, stderr = ssh.execute("[ ! -d {} ] && echo 'DNE'".format(user_loc))

            # User's directory does not exist -- create it
            if stdout:
                stdin, stdout, stderr = ssh.execute("mkdir {}".format(user_loc))

            
            # Make project_id directory
            stdin, stdout, stderr = ssh.execute("mkdir {}".format(location))

            sftp = ssh.ssh.open_sftp()
            sftp.putfo(io.StringIO(conf), conf_loc)
            sftp.putfo(io.StringIO(bngl), bngl_loc)
            sftp.putfo(io.StringIO(exp), exp_loc)
            sftp.putfo(io.StringIO(sbatch), sbatch_loc)

            stdin, stdout, stderr = ssh.execute("sbatch {}".format(sbatch_loc))


            if len(stdout) == 2:
                job_id = stdout[1].split()[-1].strip()
            else:
                job_id = stdout[0].split()[-1].strip()

            # Close SSH and SFTP connections
            ssh.__del__()

            # Add relevent data to MongoDB
            add_project(user, project_id)
            for filename, contents in zip(
                map(lambda x: x.replace(".", bnw_paths.Paths.delimiter),
                    [conf_name, bngl_name, exp_name]), [conf, bngl, exp]):
                add_input_file(user, project_id, filename, contents)

            set_slurm_id(user, project_id, job_id)
            #set_status(user, project_id, check_job_status(job_id))
            set_status(user, project_id, "PENDING")
            

            return HttpResponse(json.dumps("success"))


    # User is viewing user page normally
    if request.user.is_authenticated:
        projects = get_projects(str(request.user))
        return render(request, 'home/user.html', {"projects": list(projects.keys())})

    # User is not logged in
    else:
        return render(request, 'home/user.html')


def check_job_status(slurm_id):
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    stdin, stdout, stderr = ssh.execute("pwd")
    stdin, stdout, stderr = ssh.execute("jobstats -P -j {}".format(slurm_id))
    ssh.__del__()
    if len(stdout) == 0:
        return ""
    elif len(stdout) == 1:
        if stdout[0].startswith("JobID"):
            return ""
        return stdout[0].split("|")[-1].strip()
    else:
        return stdout[1].split("|")[-1].strip()
    

def project_name_is_valid(project_name):
    if len(project_name) > limits.NAME_LENGTH_LIMIT:
        return False
    valid = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    for char in project_name:
        if char not in valid:
            return False
    return True


def walltime_is_valid(walltime):
    try:
        wt = walltime.split(":")
        if len(wt) != 3:
            return False
        for item in wt:
            for char in item:
                if not char.isdigit():
                    return False
        wt = list(map(int, wt))
        if wt[0] < 0 or wt[0] > limits.WALLTIME_LIMIT:
            return False
        if wt[1] < 0 or wt[1] >=60:
            return False
        if wt[2] < 0 or wt[1] >= 60:
            return False
    except:
        return False

    return True


def memory_is_valid(memory):
    try:
        mem = int(memory)
        if mem < 0 or mem > limits.MEMORY_LIMIT:
            return False
    except:
        return False
    return True


def parallel_count_is_valid(parallel_count):
    if not parallel_count.isdigit():
        return False
    if int(parallel_count) < 1 or int(parallel_count) > limits.PARALLEL_COUNT_LIMIT:
        return False
    return True


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
         return ["", "", ""]

    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
        
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



def get_generational_data(output_dir):
    bestfit = "{}/{}".format(output_dir, bnw_paths.Paths.bestfit_data)
    avg = "{}/{}".format(output_dir, bnw_paths.Paths.avg_data)
    exp = "{}/{}".format(output_dir, bnw_paths.Paths.exp_data)
    obv = "{}/{}".format(output_dir, bnw_paths.Paths.obv_names)

    if not all([check_exists_monsoon(path) for path in [bestfit, avg, exp, obv]]):
        return ["", "", "", ""]

    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    
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
    
    best_csv, avg_csv, exp_csv, obv_names = get_generational_data(output_dir)

    if not all([best_csv, avg_csv, exp_csv, obv_names]):
        return render(request, "home/visualization_error.html", {"message": "The appropriate files could not be found in your BioNetFit project output folder."})
    
    obv_names = filter(lambda obv: obv, obv_names.split("\n"))
    num_gens = obv_names[-1]
    obv_names = obv_names[:-1]

    return render(request, "home/generational_plot.html", {"best_data": best_csv, "avg_data": avg_csv, "exp_data": exp_csv, "max_gen": num_gens, "observables": obv_names})


def get_fitval_data(output_dir):
    best_fitvals = "{}/{}".format(output_dir, bnw_paths.Paths.best_fitval_data)
    avg_fitvals = "{}/{}".format(output_dir, bnw_paths.Paths.avg_fitval_data)
    obv = "{}/{}".format(output_dir, bnw_paths.Paths.obv_names)

    if not all([check_exists_monsoon(path) for path in [best_fitvals, avg_fitvals, obv]]):
        return ["", "", ""]

    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    
    sftp = ssh.ssh.open_sftp()
    try:
        best_csv = io.BytesIO()
        avg_csv = io.BytesIO()
        obv_names = io.BytesIO()
        sftp.getfo(best_fitvals, best_csv)
        sftp.getfo(avg_fitvals, avg_csv)
        sftp.getfo(obv, obv_names)
    except FileNotFoundError:
        ssh.__del__()
        return ["", "", ""]

    tmp = [best_csv, avg_data, obv_names]
    return [item.getvalue().decode("ascii") for item in tmp]

def fitval_plot(request):
    username = str(request.user)
    project_name = str(request.GET.get("p", ""))

    if not project_name:
        return render(request, "home/visualization_error.html", {"message": "The project you requested could not be located."})

    output_dir = os.path.join(bnw_paths.Paths.output, username, project_name, "{}_{}".format(username, project_name)).replace("\\", "/")
    
    best_csv, avg_csv, obv_names = get_fitval_data(output_dir)
    if not all([check_exists_monsoon(path) for path in [best_csv, avg_csv, obv_names]]):
        return render(request, "home/visualization_error.html", {"message": "The appropriate files could not be found in your BioNetFit project output folder."})

    obv_names = filter(lambda obv: obv, obv_names.split("\n"))
    num_gens = obv_names[-1]
    obv_names = obv_names[:-1]

    return render(request, "home/fitval_plot.html", {"best_data": best_csv, "avg_data": avg_csv, "observables": obv_names})


def modify_conf(conf, project_id, location, bngl_loc, exp_loc, job_name):
    
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
        form = forms.RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            name = form.cleaned_data.get('name')
            org = form.cleaned_data.get('organization')
            # Email admins about new user
            message = 'Email: {}\nName: {}\nOrganization: {}\n'.format(
                username,
                name,
                org)
            try:
                mail_admins(
                    'BioNetWeb New User',
                    message,
                    fail_silently=False
                )
            except:
                pass
            # Add user to MongoDB
            add_user(username)
            
            return redirect('/login')
    else:
        form = forms.RegistrationForm()
    return render(request, 'registration/signup.html', {'form': form})


def get_project_archive(username, project_name):
    project_path = os.path.join(bnw_paths.Paths.output, username, project_name).replace("\\", "/")
    output = os.path.join(project_path, "{}.zip".format(project_name)).replace("\\", "/")
    ssh = ssh_connection.ShellHandler(bnw_paths.Paths.monsoon_ssh, secret_login.UN, secret_login.PW)
    stdin, stdout, stderr = ssh.execute("pwd")
    stdin, stdout, stderr = ssh.execute("zip {} -q -r {}".format(output, project_path))

    if len(stderr) > 0:
        ssh.__del__()
        return ""

    sftp = ssh.ssh.open_sftp()
    try:
        archive = io.BytesIO()
        sftp.getfo(output, archive)
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


def download_project_polynomial():
    with open(os.path.join("home", "polynomial.pickle"), "rb") as infile:
        return pickle.load(infile)



