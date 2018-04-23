class Option:

    def __init__(self, name, input_type, default, description, choices=None):
        self.name = name
        self.input_type = input_type
        self.description = description
        self.default = default
        self.choices = choices

    def __hash__(self):
        return hash(self.name)

general_visible = [
    Option("max_walltime", "config/walltime_input.html", "", "If a permutation is taking longer than maximum walltime, we will move on without it. Note: Many qsub systems will give your jobs lower priority as your walltime increases. Default is 01:00:00 (1 hour)."),
    Option('parallel_count', 'config/normal_input.html', "2", 'Number of models to run simultaneously when running on a personal computer. It is recommended that this is set to the number of CPU cores present in your machine. Default is 2.'),
    Option("population_size", "config/normal_input.html", "2", "Should be set to numberof CPU cores in cluster minus 1"),
    ]


general_hidden = [
    Option("seed", "config/normal_input.html", "", "Seed for BioNetFit's random number generator.  Comment this option out in order to use a different seed every time. Note: This seed only applies to BioNetFit's random number generator. It does not affect NFsim or BioNetGen. To give NFsim a seed, set seed=### in your simulation command or .rnf file. Default is no user-specified seed (i.e.,the seed is determined automatically)."),
    Option("max_retries", "config/normal_input.html", "3", "Sometimes a generation must be re-run because there were too many simulations which did not finish successfully.  This often happens because they hit the specified maximum walltime. max_retries is the number of times a generation will be run before BioNetFit gives up. Default is 3."),
    Option("make_plots", "config/bool_input.html", "", "Whether or not BioNetFit will output plots when results are ready. Default is 0."),
    Option("delete_old_files", "config/bool_input.html", "", "BioNetFit results can use a lot of disk space.  Enabling this option will delete unnecessary files (.net, .bngl, .xml, .cdat, etc) as a run progresses. We note that if this option is turned on, BioNetFit may not be able to supply you with a model or .net file containing best-fit parameters at the end of the fitting run."),
    ]


fitting_visible = [
    Option("max_generations", "config/normal_input.html", "", "The maximum number of iterations or generations (Gmax). BioNetFit will execute this number of generations unless it quits earlier due to satisfaction of a stopping condition."),
    Option("permutations", "config/normal_input.html", "", "The number of parameter value sets or population size or number of permutations (N). At each iteration, N simulation jobs will be performed."),
    ]


fitting_hidden = [
    Option("smoothing", "config/normal_input.html", "1", "Number of replicate simulation runs. The default value is 1. Multiple simulation runs are useful for smoothing the results of stochastic simulation. NB: Setting this parameter to 10 will increase the cost of simulation by an order of magnitude."),
    Option("objfunc", "config/listbox_input.html", "1", "y(x)= measured value at condition x y[prime](x)= simulated value at condition x The objective function is a sum of terms over all x values. The terms can have the forms indicated below: 1:(y(x)-y[prime](x))[squared] 2: ((y(x)-y[prime](x))/y_SD(x))[squared] 3:((y(x)-y[prime](x))/y(x))[squared] 4:((y(x)-y[prime](x))/ybar)[squared] The objective function is selected by setting objfunc to one of the index values above. A setting of objfunc=1 indicates that the objective function is the sum-of-squares function (i.e., nonlinear least squares fitting). A setting of objfunc=2 indicates that the objective function is the chi-square function (i.e., weighted nonlinear least squares fitting). For this option, y values in .exp files must be accompanied by y_SD values. The default setting is 1.", choices=[str(i) for i in range(1, 5)]),
    Option("extra_weight", "config/listbox_input.html", "0", "When selecting parents to breed, they are already weighted such that runs with better goodness-of-fit are more likely to be chosen. If you would like to weight the selection even more, increase this value. Note that more weight will make it less likely that different parents will be selected for breeding. Note: Values must be in the range 0-10. Default value is 0.", choices=[str(i) for i in range(11)]),
    Option("swap_rate", "config/normal_input.html", "0.5", "This parameter sets the 'recombination' rate (Q1). It is a probability, so values must be between 0 and 1. The default settingis 0.5."),
    Option("max_parents", "config/normal_input.html", "", "This parameter sets the maximum number of 'parents' to be used in 'breeding.' By default, this parameter is equal to the population size (N)."),
    Option("keep_parents", "config/normal_input.html", "0", "This parameter determines the number of top-ranked parents (parameter value sets) that will be carried over to the next iteration. Default is 0."),
    Option("min_objfunc_value", "config/normal_input.html", "0", "If simulation results for a given parameter value set produce a function evaluation less than the value specified for this parameter, fitting will stop. The default is no stopping condition (i.e., this parameter is set to 0)."),
    Option("max_objfunc_value", "config/normal_input.html", "", "If simulation results for a given parameter value set produce a function evaluation greater than the value specified for this parameter, the parameter value set will not be used in 'breeding.' The default is no limit."),
    Option("first_gen_permutations", "config/normal_input.html", "", "Number of permutations to run in your first generation. This option allows you to start a fitting run with greater diversity. This setting will have the same value as permutations by default."),
    Option("log_transform_sim_data", "config/normal_input.html", "", "If this option is set to an integer value, all simulation output will be log transformed using the specified value as the transformation base. This transformation takes place prior to cost function evaluation."),
    Option("fit_type", "config/normal_input.html", "", "Here ga is genetic algorithm, de is differential evolution, sa is simulated annealing, pso is particle swarm"),
    Option("output_every", "config/normal_input.html", "", "In an asynchronous fit, output a run summary every n simulations"),
    Option("num_islands", "config/normal_input.html", "", "In Differential Evolution (de), the number of islands"),
    Option("mutate_type", "config/normal_input.html", "", "In (differential evolution) DE and (simulated annealing) SA, the mutation type, such as [4]"),
    Option("cr", "config/normal_input.html", "", "In (differential evolution) DE and (simulated annealing) SA, the crossover rate"),
    Option("migration_frequency", "config/normal_input.html", "", "In (differential evolution) DE, how often particles migrate between islands"),
    Option("num_to_migrate", "config/normal_input.html", "", "In (differential evolution) DE, how many points to migrate during crossover"),
    Option("inertia", "config/normal_input.html", "", "In (particle swarm) PSO, the inertia"),
    Option("cognitive", "config/normal_input.html", "", "In (particle swarm) PSO, the cognitive factor"),
    Option("social", "config/normal_input.html", "", "The social factor in PSO"),
    Option("nmin", "config/normal_input.html", "", "[nmax is 20, thus nmin is 80]?"),
    Option("nmax", "config/normal_input.html", "", "[nmax is 20, thus nmin is 80]?"),
    Option("inertiaInit", "config/normal_input.html", "", "In enhanced inertia, the initial inertia [i.e. is 1]"),
    Option("inertiaFinal", "config/normal_input.html", "", "In enhanced inertia, the final inertia [i.e. is 0.1]"),
    Option("abs_tolerance", "config/normal_input.html", "", "Tolerances for enhanced (particle swarm) PSO stop [i.e. 10e-4]"),
    Option("rel_tolerance", "config/normal_input.html", "", "Tolerances for enhanced (particle swarm) PSO stop [i.e. 10e-4]"),
    Option("mutate_qpso", "config/normal_input.html", "", "Whether or not to enable mutations in QPSO"),
    Option("topology", "config/normal_input.html", "", "Swarm tolopogy in particle swarm or island migration topology in differential evolution can be either ring or toroidal or star or fullyconnected or mesh or tree"),
    Option("pso_type", "config/normal_input.html", "", "PSO (particle swarm) variant, can be bbpso, bbpsoexp, pso (normal pso), qpso (quantum behaved particle swarm)"),
    Option("synchronicity", "config/bool_input.html", "", "1/0 is synchronous/asynchronous"),
    Option("enhanced_stop", "config/bool_input.html", "", "Whether or not to use enhanced stop criteria in PSO (not sure if this works well)"),
    Option("enhanced_inertia", "config/bool_input.html", "", "Whether or not to use enhanced inertia in PSO"),
    Option("use_pipes", "config/bool_input.html", "", "checked to run in windows, pipes"),
    Option("divide_by_init", "config/bool_input.html", "", "This option instructs BioNetFit, before cost function evaluation, to divide each model output by the first listed value of the output in the .gdat (or .scan) file, i.e., by the top numerical value in the .gdat (or .scan) file. This feature is useful when the first value listed is, for example, the basal steady-state value and the experimental data being used in fitting consists of fold-change measurements made relative to the basal steady state."),
    Option("stop_when_stalled", "config/bool_input.html", "checked", "If this parameter is set to 1 (default setting) BioNetFit will stop the fitting run if new parameter value sets are identical to old parameter value sets after 'breeding.' This situation would only be expected to arise if the rate of 'mutation' is set to 0."),
    Option("standardize_sim_data", "config/bool_input.html", "", "This option instructs BioNetFit to standardize simulation output to a mean of 0, using the following formula: <y[x] = [y[x] minus ybar] / stdev[y]> This standardization happens prior to cost function evaluation."),
    Option("standardize_exp_data", "config/bool_input.html", "", "Similar to the above option, but in regards to experimental data (.exp file)."),
    Option("force_different_parents", "config/bool_input.html", "checked", "This parameter determines whether a 'parent' is allowed to 'breed' with itself. If self-breeding is allowed, some parameter value sets may be unchanged from iteration to iteration. The default setting is 1."),
    ]


cluster_hidden = [
    Option("cluster_command", "config/listbox_input.html", "", "The user may specify the command to be used to submit a job for processing. However, in most cases, this is not necessary. BioNetFit is designed to automatically determine which command to use. Acceptable options are limited to 'sbatch' and 'qsub.'", choices=["sbatch", "qsub"]),
    Option("cluster_software", "config/listbox_input.html", "", "The user may specify the cluster platform being used. However, in most cases, this is not necessary. BioNetFit is designed to automatically determine which cluster platform is being used. Acceptable options are 'slurm,' 'torque,' and 'ge.'", choices=["slurm", "torque", "ge", "BNF2mpi"]),
    Option("pe_name", "config/normal_input.html", "", "The user may specify the parallel environment being used on the cluster. This is generally necessary on an SGE-based cluster. In general, this setting must be obtained from the cluster administrator; however, a typical setting is 'orte.'"),
    Option("queue_name", "config/normal_input.html", "", "The user may specify the work queue being used on the cluster. In general, this setting must be obtained from the cluster administrator; however, a typical setting is 'all.'"),
    Option("account_name", "config/normal_input.html", "", "The user may specify the account name being used on the cluster. This setting must be obtained from the cluster administrator. The account name is typically used to meter cluster usage."),
    Option("job_sleep", "config/normal_input.html", "1", "How many seconds to wait between sending off cluster jobs. This is useful because cluster schedulers sometimes fail to submit jobs properly when they are submitted in close succession. He default setting is 1."),
    Option("multisim", "config/normal_input.html", "1", "Number of simulations to run with each thread. The simulations will be run in serial. If your simulations finish quickly and the permutations option is set to a large value, you may want to set multisim to a value greater than 1, which will limit the number of jobs submitted. This will avoid the idle time between job submissions. The default setting is 1."),
    Option("use_cluster", "config/bool_input.html", "unchecked", "This option should be set to 1 if you are running on a cluster. It is set to 0 by default."),
    Option("save_cluster_output", "config/bool_input.html", "unchecked", "This option controls message output from the cluster job scheduler. Its default setting is 0 (no output). Setting this option to 1 may be useful for debugging and/or for reporting bugs or problems."),
    Option("run_job_from_worknode", "config/bool_input.html", "", "Whether or not your cluster allows you to submit cluster jobs FROM working nodes. BioNetFit is designed to automatically determine which setting to use, so in most cases the user will not need to set this option. Set to 0 if you can only submit cluster jobs from the submission node (common on SGE clusters). Set to 1 if you can submit cluster jobs from work nodes (common on Torque/PBS and SLURM clusters)."),
    ]


path_hidden = [
    Option("model", "config/normal_input.html", "", "Absolute path to your model file"),
    Option("exp_file", "config/normal_input.html", "", "Absolute path to your .exp file. You may specify this option multiple times for multiple .exp files"),
    Option("output_dir", "config/normal_input.html", "", "Absolute path where you want your output to go"),
    Option("bng_command", "config/normal_input.html", "", "Absolute path to your BioNetGen executable"),
    Option("job_name", "config/normal_input.html", "", "This is the job name, and name of the directory that will contain your results."),
    ]


display_hidden = [
    Option("verbosity", "config/listbox_input.html", "", "How much information to display about run progress.  0 = no information, 4 = way more information than you are likely to need. 1 or 2 is recommended. Default is 1.", choices=[str(i) for i in range(5)]),
    Option("ask_create", "config/bool_input.html", "", "Whether or not to ask when creating a new output directory. Default is 1."),
    Option("ask_overwrite", "config/bool_input.html", "", "Whether or not to ask when overwriting existing job output. Default is 1. Warning: Turning this off can be dangerous!"),
    Option("show_welcome_message", "config/bool_input.html", "", "Whether or not to show a welcome message when running BioNetFit. Default is 1."),
    ]
