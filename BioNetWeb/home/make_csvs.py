import glob
import sys
import os

AVG_GDAT = "average.gdat"
BEST_PERM= "best_perm.txt"
IGNORE = [AVG_GDAT, BEST_PERM]


'''
============================ Creating Average GDATs ============================
'''
def make_avg_gdats(directories):
    global IGNORE
    global AVG_GDAT
    for directory in directories:
        out = _get_average_values(directory)
        
        with open(os.path.join(directory, "average.gdat"), "w") as f:
            f.write("#\t")
            for field in out:
                length = len(out[field])
                f.write(field + "\t")
            f.write("\n")

            for i in range(length):
                for field in out:
                    f.write(format(out[field][i], ".12e") + "\t")
                f.write("\n")


def _get_average_values(directory):
    out = {}
    for file in glob.glob("{0}/*.gdat".format(directory)):
        for item in IGNORE:
            if file.endswith(item):
                continue
        with open(file, "rU") as f:
            lines = f.readlines()
        fields = lines[0].strip().split()[1:]
        for field in fields:
            if field not in out:
                out[field] = [0 for x in range(len(lines[1:]))]
        for i, line in enumerate(lines[1:]):
            values = line.strip().split()
            for j, value in enumerate(values):
                out[fields[j]][i] += float(value)
    for field in out:
        if len(out[field]) == 0:
            print(field)
        for i in range(len(out[field])):
            out[field][i] /= len(glob.glob("{0}/*.gdat".format(directory)))
    return out

'''
================================================================================
'''



def get_best_perms(directories, exp_file):
    global IGNORE
    global BEST_PERM
    exp = read_gdat(exp_file)
    for directory in directories:
        best_fit_value = 100
        best_perm = ""
        for file in glob.glob("{0}/*.gdat".format(directory)):
            for item in IGNORE:
                if file.endswith(item):
                    continue
            out = read_gdat(file)
            average_fit_val = 0
            divisor = 0
            for field in out:
                if field in exp:
                    average_fit_val += fit_value(out[field], exp[field])
                    divisor += 1
            if divisor == 0:
                continue
            average_fit_val /= divisor
            if average_fit_val < best_fit_value:
                best_fit_value = average_fit_val
                best_perm = file
                
        with open(os.path.join(directory, BEST_PERM), "w") as f:
            f.write(best_perm)

            
def make_best_fitval_csv(output_dir, directories, exp_file):
    global BEST_PERM
    exp = read_gdat(exp_file)
    out = {}
    for directory in directories:
        out[os.path.basename(directory)] = {}
        with open(os.path.join(directory, BEST_PERM), "rU") as f:
            best_perm = f.readline().strip()

        perm = read_gdat(best_perm)
        for field in perm:
            if field in exp and field != "time":
                out[os.path.basename(directory)][field] = fit_value(perm[field], exp[field])
    for d in out:
        avg = 0
        for field in out[d]:
            avg += out[d][field]
        avg /= len(out[d])
        out[d]["average"] = avg

    with open(os.path.join(output_dir, "best_fitvals.csv"), "w") as f:
        f.write("gen,name,val\\n")
        for d in out:
            for field in out[d]:
                f.write("{0},{1},{2}\\n".format(d,field,format(out[d][field], ".12e")))


            
def make_avg_fitval_csv(output_dir, directories, exp_file):
    global AVG_GDAT
    exp = read_gdat(exp_file)
    out = {}
    for directory in directories:
        out[os.path.basename(directory)] = {}
        perm = read_gdat(os.path.join(directory, AVG_GDAT))
        for field in perm:
            if field in exp and field != "time":
                out[os.path.basename(directory)][field] = fit_value(perm[field], exp[field])
    for d in out:
        avg = 0
        for field in out[d]:
            avg += out[d][field]
        avg /= len(out[d])
        out[d]["average"] = avg

    with open(os.path.join(output_dir, "avg_fitvals.csv"), "w") as f:
        f.write("gen,name,val\\n")
        for d in out:
            for field in out[d]:
                f.write("{0},{1},{2}\\n".format(d,field,format(out[d][field], ".12e")))


'''
============================== Generational Graph ==============================
'''
def make_perm_csv(data, outfile_name, output_dir):
    times = data["1"]["time"]
    with open(os.path.join(output_dir, outfile_name), "w") as outfile:
        outfile.write("gen,name,value,time\\n")
        for gen in data:
            for name in data[gen]:
                if name == "time":
                    continue
                for idx, datum in enumerate(data[gen][name]):
                    outfile.write("{0},{1},{2},{3}\\n".format(gen,name,datum,times[idx]))


# Takes in list of obvs in EXP file, dict where key=directory, value=gdat
def read_perms(exp_fields, perms):
    out = {}
    for perm in perms:
        obv = {}
        for field in exp_fields:
            obv[field] = []
        with open(os.path.join(perm, perms[perm]), "rU") as f:
            # Calculate which fields to look at in the gdat files
            indices = []
            fields = f.readline().split()
            for field in exp_fields:
                indices.append(fields.index(field)-1)
            for line in f:
                data = line.split()
                for idx, index in enumerate(indices):
                    val = float(data[index])
                    obv[exp_fields[idx]].append(val)
        out[os.path.basename(perm)] = obv
    return out


def best_perm_txt_to_dict(directories):
    global BEST_PERM
    out = {}
    for directory in directories:
        with open(os.path.join(directory, BEST_PERM), "rU") as f:
            file = f.readline().strip()
        out[directory] = os.path.basename(file)
    return out


def avg_perm_to_dict(directories):
    global AVG_GDAT
    out = {}
    for directory in directories:
        out[directory] = AVG_GDAT
    return out

'''
================================================================================
'''


def write_observables(data, output_dir):
    observables = set()
    for obv in data:
        if obv == "time":
            continue
        observables.add(obv)
    with open(os.path.join("{0}".format(output_dir), "obv_names.txt"), "w") as outfile:
        for obv in observables:
            outfile.write(obv + "\n")


def make_exp_csv(exp_file, output_dir):
    exp = read_gdat(exp_file)
    times = exp["time"]
    with open(os.path.join(output_dir, "exp_data.csv"), "w") as f:
        f.write("name,value,time\\n")
        for field in exp:
            if field != "time":
                for idx, datum in enumerate(exp[field]):
                    f.write("{0},{1},{2}\\n".format(field,datum,times[idx]))
    return list(exp.keys())


def make_bestfit_csv(exp_fields, bestfit_gdat, output_dir):
    bestfit = read_gdat(bestfit_gdat)
    times = bestfit["time"]
    with open(os.path.join(output_dir, "bestfit.csv"), "w") as f:
        f.write("name,value,time\\n")
        for field in bestfit:
            if field != "time":
                for idx, datum in enumerate(bestfit[field]):
                    f.write("{0},{1},{2}\\n".format(field,datum,times[idx]))
        

def read_gdat(file):
    out = {}
    with open(file, "rU") as f:
        lines = f.readlines()
    fields = lines[0].strip().split()[1:]
    for field in fields:
        out[field] = []
    for line in lines[1:]:
        values = line.strip().split()
        for i, value in enumerate(values):
            out[fields[i]].append(float(value))
    return out


def fit_value(obv_list, exp_list):
    numerator = 0
    denominator = 0
    for i in range(len(obv_list)):
        numerator += ((exp_list[i] - obv_list[i])**2)
        denominator += (exp_list[i]**2)

    return numerator / denominator


def get_directories(main_folder):
    return [os.path.abspath(os.path.join(main_folder, name))
            for name in os.listdir(main_folder)
            if os.path.isdir(os.path.join(main_folder, name))
            and name.isdigit()]


def main(output_dir, exp_file, bestfit_gdat):

    """Make CSVs for bestfit visualization"""
    exp_fields = make_exp_csv(exp_file, output_dir)
    make_bestfit_csv(exp_fields, bestfit_gdat, output_dir)

    """Gather any data needed for making CSV files"""
    directories = get_directories(output_dir)   # Get generational directories
    make_avg_gdats(directories)                 # Make a GDAT file in each generational directory with average values from all perms
    get_best_perms(directories, exp_file)       # Make a txt file in each generational directory containing path to best GDAT file for that generation

    """Make CSVs for fit-value visualization"""
    try:
        make_best_fitval_csv(output_dir, directories, exp_file)
        make_avg_fitval_csv(output_dir, directories, exp_file)
    except:
        pass

    """Make CSVs for generational visualization"""
    best_perms = best_perm_txt_to_dict(directories)
    avg_perms = avg_perm_to_dict(directories)
    best_data = read_perms(exp_fields, best_perms)
    avg_data = read_perms(exp_fields, avg_perms)
    make_perm_csv(best_data, "best_data.csv", output_dir)
    make_perm_csv(avg_data, "avg_data.csv", output_dir)

    

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[2])
                
