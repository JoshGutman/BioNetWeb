class Paths:

    '''
    bionetfit = "/scratch/jng86/BioNetFit2_pull1/bin/BioNetFit2"
    bin_loc = "/scratch/jng86/BioNetFit2_pull1/bin/"
    bng_command = "/scratch/jng86/BioNetFit2_pull1/Simulators/BNG2.pl"
    output = "/scratch/jng86/bnw/"
    monsoon_ssh = "monsoon.hpc.nau.edu"
    '''
    bionetfit = "/scratch/bionetfit/BioNetFit2_pull1/bin/BioNetFit2"
    bin_loc = "/scratch/bionetfit/BioNetFit2_pull1/bin/"
    bng_command = "/scratch/bionetfit/BioNetFit2_pull1/Simulators/BNG2.pl"
    output = "/scratch/bionetfit/bnw/"
    monsoon_ssh = "bionetfithead.cefns.nau.edu"
    delimiter = "__dot__"    # MongoDB doesn't allow "." in key names


    def make_sbatch(name, output, time_id, walltime, ntasks, conf_loc):
        
        sbatch = """#!/bin/bash
#SBATCH --job-name={}
#SBATCH --output={}/{}_output.txt
#SBATCH --time={}
#SBATCH --workdir={}
#SBATCH --mem=10000
#SBATCH --ntasks={}


module purge
module load gcc/5.4.0
module load openmpi/1.10.2
module load glibc/2.23
module load boost/1.65.0-gcc-5.4.0

./BioNetFit2 -a cluster -c {}

""".format(name, output, time_id, walltime, Paths.bin_loc, ntasks, conf_loc)

        return sbatch


if __name__ == "__main__":

    print(Paths.make_sbatch("jng86_1234", "/scratch/jng86/bnw/1234", "1234", "12:30:00", "33", "/scrach/jng86/bnw/1234/1234.conf"))
