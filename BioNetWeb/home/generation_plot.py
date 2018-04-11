import os
import glob


# Return dict where key = field name, value = numpy array of values
def read_exp(exp_file):
    obv = {}
    with open(exp_file, "rU") as infile:
        fields = infile.readline().split()[1:]
        for field in fields:
            obv[field] = []
        for line in infile:
            data = line.split()
            for idx, field in enumerate(fields):
                obv[field].append(float(data[idx]))
    return obv


def get_directories(main_folder):
    return [os.path.abspath(os.path.join(main_folder, name))
            for name in os.listdir(main_folder)
            if os.path.isdir(os.path.join(main_folder, name))
            and name.isdigit()]


def get_best_perms(directories):
    FILE_NAME = "perm_model_diff.txt"
    out = {}
    for d in directories:
        with open(os.path.join(d, FILE_NAME), "rU") as f:
            f.readline()
            out[d] = f.readline().split()[0]
    return out

def get_average_perms(directories):
    FILE_NAME = "perm_model_diff.txt"
    out = {}
    for d in directories:
        try:
            with open(os.path.join(d, FILE_NAME), "rU") as f:
                lines = f.readlines()
                average = lines[len(lines)-2]
                out[d] = average.split()[0]
        except FileNotFoundError:
    return out


'''
def get_best_perms(directories):
    FILE_NAME = "Ranked_results.txt"
    out = {}
    for d in directories:
        with open(os.path.join(d, FILE_NAME), "rU") as f:
            f.readline()
            out[d] = f.readline().split()[0]
    return out
'''


def read_best_perms(exp_fields, best_perms):

    out = {}
    
    mins = {}
    maxs = {}
    for field in exp_fields:
        mins[field] = 999999999999999999999
        maxs[field] = -999999999999999999999

    for perm in best_perms:

        obv = {}
        for field in exp_fields:
            obv[field] = []
        
        for file in glob.glob("{0}/*{1}.gdat".format(perm, best_perms[perm])):
            with open(file, "rU") as f:

                # Calculate which fields to look at in the gdat files
                indeces = []
                fields = f.readline().split()
                for field in exp_fields:
                    indeces.append(fields.index(field)-1)

                for line in f:
                    data = line.split()
                    for idx, index in enumerate(indeces):
                        val = float(data[index])
                        if val < mins[exp_fields[idx]]:
                            mins[exp_fields[idx]] = val
                        if val > maxs[exp_fields[idx]]:
                            maxs[exp_fields[idx]] = val
                            
                        obv[exp_fields[idx]].append(val)

        out[int(os.path.basename(perm))] = obv

    return out



def make_perm_csv(data, is_best, output_dir):
    times = data[1]["time"]

    if is_best:
        outfile_name = "{0}/best_data.csv".format(output_dir)
    else:
        outfile_name = "{0}/avg_data.csv".format(output_dir)

    with open(outfile_name, "w") as outfile:
        outfile.write("gen,name,value,time\n")
        for gen in data:
            for name in data[gen]:
                if name == "time":
                    continue
                for idx, datum in enumerate(data[gen][name]):
                    outfile.write("{0},{1},{2},{3}\n".format(gen,name,datum,times[idx]))

    
def make_exp_csv(data, output_dir):
    times = data["time"]
    outfile_name = "{0}/exp_data.csv".format(output_dir)

    with open(outfile_name, "w") as outfile:
        outfile.write("name,value,time\\n")
        for name in data:
            if name == "time":
                continue
            for idx, datum in enumerate(data[name]):
                outfile.write("{0},{1},{2}\\n".format(name,datum,times[idx]))


def write_observables(data, output_dir, num_gens):
    observables = set()
    for obv in data:
        if obv == "time":
            continue
        observables.add(obv)
    with open("{}/obv_names.txt".format(output_dir), "w") as outfile:
        for obv in observables:
            outfile.write(obv + "\n")
        outfile.write(num_gens + "\n")



if __name__ == "__main__":

    import sys

    # exp file path
    # output directory path

    exp_data = read_exp(sys.argv[1])
    dirs = get_directories(sys.argv[2])
    best_perms = get_best_perms(dirs)
    avg_perms = get_average_perms(dirs)

    avg_data = read_best_perms(list(exp_data.keys()), avg_perms)
    best_data = read_best_perms(list(exp_data.keys()), best_perms)
    
    make_perm_csv(best_data, True, sys.argv[2])
    make_perm_csv(avg_data, False, sys.argv[2])
    make_exp_csv(exp_data, sys.argv[2])
    write_observables(exp_data, sys.argv[2], len(dirs))
