import paramiko
import sys
import os
import getpass
import re
import time


class ShellHandler:

    def __init__(self, host, user, psw):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=22)

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        self.ssh.close()

    def execute(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish = 'end of stdOUT buffer. finished with exit status'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        exit_status = 0
        for line in self.stdout:
            if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
                # up for now filled with shell junk from stdin
                shout = []
            elif str(line).startswith(finish):
                # our finish command ends with the exit status
                exit_status = int(str(line).rsplit(maxsplit=1)[1])
                if exit_status:
                    # stderr is combined with stdout.
                    # thus, swap sherr with shout in a case of failure.
                    sherr = shout
                    shout = []
                break
            else:
                # get rid of 'coloring and formatting' special characters
                shout.append(re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).
                             replace('\b', '').replace('\r', ''))

        # first and last lines of shout/sherr contain a prompt
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        return shin, shout, sherr






if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage:\npython {} .conf .bngl .exp".format(__file__))
        sys.exit()
        
    conf = sys.argv[1]
    bngl = sys.argv[2]
    exp = sys.argv[3]

    conf_bn = os.path.basename(conf)
    bngl_bn = os.path.basename(bngl)
    exp_bn = os.path.basename(exp)


    un = input("Enter username: ")
    pw = getpass.getpass(prompt="Enter password: ")

    ssh = ShellHandler("monsoon.hpc.nau.edu", un, pw)
    
    sftp = ssh.ssh.open_sftp()
    print("SFTP connection established...")

    print("Transferring .conf file...", end="")
    sftp.put(conf, "/scratch/jng86/{}".format(conf_bn))
    print("Done")

    print("Transferring .bngl file...", end="")
    sftp.put(bngl, "/scratch/jng86/{}".format(bngl_bn))
    print("Done")

    print("Transferring .exp file...", end="")
    sftp.put(exp, "/scratch/jng86/{}".format(exp_bn))
    print("Done")

    print("Loading appropriate modules for BioNetFit...", end="")
    ssh.execute("module purge")
    ssh.execute("module load gcc/5.4.0")
    ssh.execute("module load openmpi/1.10.2")
    ssh.execute("module load glibc/2.23")
    ssh.execute("module load boost/1.65.0-gcc-5.4.0")
    print("Done")

    ssh.execute("cd /scratch/jng86/")

    print("Running BioNetFit as a SLURM job...")
    sin1, sout1, serr1 = ssh.execute("sbatch job.sh")
    print("\n".join(sout1[:-1]))

    time.sleep(1)
    sin2, sout2, serr2 = ssh.execute("jobstats -u jng86")
    print("\n".join(sout2[:-1]))

    job_num = sout1[0].split()[-1].strip()
    print("Pulling SLURM job file \"job.sh\" from Monsoon...", end="")
    #"{}/job.sh".format(os.path.abspath(os.getcwd()).replace("\\", "/"))
    sftp.get("/scratch/jng86/job.sh", os.path.join(os.path.abspath(os.getcwd()), "job.sh"))
    print("Done")

    print("Closing SSH and SFTP connections...", end="")
    ssh.__del__()
    print("Done")



