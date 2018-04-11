def read_gdat(gdat):
    out = {}
    with open(gdat, "rU") as f:
        fields = f.readline().split()[1:]
        for field in fields:
            out[field] = []
        for line in f:
            data = line.split()
            for idx, datum in enumerate(data):
                out[fields[idx]].append(datum)
    return out


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


def write_csv(data, output_dir):
    outfile_name = "{0}/bestfit.csv".format(output_dir)
    time = data["time"]

    with open(outfile_name, "w") as outfile:
        outfile.write("name,value,time\\n")
        for obv in data:
            if obv == "time":
                continue
            for idx, datum in enumerate(data[obv]):
                outfile.write("{0},{1},{2}\\n".format(obv, datum, time[idx]))
        
            
def write_observables(data, output_dir):
    observables = set()
    for obv in data:
        if obv == "time":
            continue
        observables.add(obv)
    with open("{0}/obv_names.txt".format(output_dir), "w") as outfile:
        for obv in observables:
            outfile.write(obv + "\n")


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


if __name__ == "__main__":
    import sys
    # bestfit gdat file path
    # exp file path
    # Output dir path

    gdat_path = sys.argv[1]
    exp_path = sys.argv[2]
    output_dir = sys.argv[3]
    
    gdat = read_gdat(gdat_path)
    exp = read_exp(exp_path)
    make_exp_csv(exp, output_dir)
    write_csv(gdat, output_dir)
    write_observables(exp, output_dir)
