class Paths:

    bionetfit = "/scratch/bionetfit/BioNetFit2_pull1/bin/BioNetFit2"
    bin_loc = "/scratch/bionetfit/BioNetFit2_pull1/bin/"
    bng_command = "/scratch/bionetfit/BioNetFit2_pull1/Simulators/BNG2.pl"
    output = "/scratch/bionetfit/bnw/"
    monsoon_ssh = "bionetfithead.cefns.nau.edu"
    
    make_csvs_script = "/scratch/bionetfit/make_csvs.py"
    bestfit_data = "bestfit.csv"
    best_data = "best_data.csv"
    avg_data = "avg_data.csv"
    exp_data = "exp_data.csv"
    obv_names = "obv_names.txt"
    best_fitval_data = "best_fitvals.csv"
    avg_fitval_data = "avg_fitvals.csv"
    
    delimiter = "__dot__"    # MongoDB doesn't allow "." in key names


    def make_sbatch(name, output, time_id, walltime, memory, ntasks, conf_loc, exp_file, bestfit_gdat):
        
        sbatch = """#!/bin/bash
#SBATCH --job-name={}
#SBATCH --output={}/{}_output.txt
#SBATCH --time={}
#SBATCH --workdir={}
#SBATCH --mem={}
#SBATCH --ntasks={}


module purge
module load gcc/5.4.0
module load openmpi/1.10.2
module load glibc/2.23
module load boost/1.65.0-gcc-5.4.0

./BioNetFit2 -a cluster -c {}

module load anaconda/3.latest

python {} {}/{} {} {}

""".format(name, output, time_id, walltime, Paths.bin_loc, memory, ntasks, conf_loc,
           Paths.make_csvs_script, output, name, exp_file, bestfit_gdat)

        return sbatch


if __name__ == "__main__":

    print(Paths.make_sbatch("jng86_1234", "/scratch/jng86/bnw/1234", "1234", "12:30:00", "12", "33", "/scratch/jng86/bnw/1234/1234.conf", "/scratch/jng86/bnw/1234/1234.exp", "/scratch/jng86/bnw/1234/jng86_1234/1234.gdat"))
