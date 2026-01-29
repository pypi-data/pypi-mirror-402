# Installation

Follow this [guide](https://docs.astral.sh/uv/getting-started/installation/) to install UV. 

# Running it

To run the entrypoint, run the following command.

```bash
 uv run -m semistaticsim.groundtruth.main
```

You can set the target amount of simulation time to collect as well as the scan size. 
The bigger the scan size, the higher the RAM usage and jitting time, but it has the *potential* to go faster if you want to collect a lot of simulation time.

After collecting the data, plot the groundtruth of the first pickupable across all its valid receptacles: 

```bash
uv run -m semistaticsim.groundtruth.viz
```

To run the ai2thor simulation, you can use

```bash
 uv run -m semistaticsim.keyboardcontrol.main_skillsim
```

### On the cluster

*Migue's installaton*:

I had issues installing the environment using Conda in the cluster. So I followed slightly different steps:

First I installed libmamba following the instructions listed [here](https://docs.mila.quebec/Userguide_portability.html#mamba). After that I created these aliases so conda is not running by default in my session

```bash
# In .bashrc

# Hook to activate conda base
alias conda-hook='eval "$($HOME/miniconda3/bin/conda shell.$(basename     $SHELL) hook)"'
# Hook to activate envirnment when running interactive
alias semistatic-inter="cd ~; cd $HOME/projects/SemiStaticSim; conda-hook; conda activate sss; export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH; export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib"
# Hook to activate envirnment when running in multirun
alias semistatic-cluster="cd ~; cd $HOME/projects/SemiStaticSim; module load python/3.10"
```

After installing `libmamba`, I installed the environment as follows:

```bash
conda-hook
conda create -n sss -c conda-forge python=3.12 libvulkan-loader conda-forge::uv --solver=libmamba
rm -rf ./generated_data && mkdir -p $SCRATCH/perpetua_data/sss/generated_data && ln -s $SCRATCH/perpetua_data/sss/generated_data ./generated_data
```

*Charlie's installaton*:

```bash
module load anaconda/3
conda create -n sss -c conda-forge python=3.12 libvulkan1 uv
rm -rf ./generated_data && mkdir -p $SCRATCH/perpetua_data/sss/generated_data && ln -s $SCRATCH/perpetua_data/sss/generated_data ./generated_data
```

#### Single job on an interactive compute node:

*Migue's running scheme*:

```bash
semistatic-inter
# uv run -m semistaticsim.[groundtruth.main | keyboardcontro.main_skillsim] [hydra overrides]
```

*Charlie's running scheme*:

```bash
module load anaconda/3 && conda activate sss
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
# uv run -m semistaticsim.[groundtruth.main | keyboardcontro.main_skillsim] [hydra overrides]
```

#### Multirun:

For both GT and Rendering, there's a lot of SLURM setup at first, and then the last few args will be actual hydra overrides.
Note: if you have loaded `anaconda/3`, you WILL break the multirun. You need to unload all modules, and only load `python/3.10` and launch using `uv`. The `anaconda/3` module will be automatically loaded by the scripts themselves, inside `semistaticsim/spoof_hydra.py`.

NOTE: This is set to launch on partition `main`. On the Mila cluster, this means that only 1 batch of 4 tasks will run at once.
Swap to partition `long` if you wish for massive parallelism (but less priority).

*Miguel's running scheme*: Same but do: `git checkout miguel/cluster`

Groundtruth: 

```bash
module load python/3.10
uv run -m semistaticsim.groundtruth.main --multirun hydra/launcher=sbatch +hydra/sweep=sbatch hydra.launcher._target_=hydra_plugins.packed_launcher.packedlauncher.SlurmLauncher hydra.launcher.tasks_per_node=4 +hydra.launcher.timeout_min=59 hydra.launcher.gres=gpu:1 +hydra.launcher.constraint='40gb|48gb'  hydra.launcher.cpus_per_task=2 hydra.launcher.mem_gb=40 hydra.launcher.array_parallelism=300 hydra.launcher.partition=main hydra.launcher.name=SSS_GT procthor_index=range\(0,8\)
```

Rendering:

```bash
module load python/3.10
uv run -m semistaticsim.keyboardcontrol.main_skillsim --multirun hydra/launcher=sbatch +hydra/sweep=sbatch hydra.launcher._target_=hydra_plugins.packed_launcher.packedlauncher.SlurmLauncher hydra.launcher.tasks_per_node=4 +hydra.launcher.timeout_min=59 hydra.launcher.gres=gpu:1 +hydra.launcher.constraint='40gb|48gb'  hydra.launcher.cpus_per_task=2 hydra.launcher.mem_gb=40 hydra.launcher.array_parallelism=300 hydra.launcher.partition=main hydra.launcher.name=SSS_PRIV mode=auto index=range\(0,4\)
```


## How-to

Features are based around varying the level of scene-to-scene semantic transfer. Every simulator step, some dt time elapses. When the `duration_left` reaches 0, the transition model selects the next receptacle that the object will transition to. Then, the duration model sampels the amount of tiem that the objet will spend in that new receptacle.

Duration model:

1. even is "evenly spread duration of all steps"
2. instant is "spend NO time at this place, immediately transition at the next step" (this is what flowmaps currently has in your 2D simulator)
3. deterministic is "randomly split the day among all steps"
4. gaussian is the same as deterministic with some gaussian noise

Transition model:

1. "fixed_canonical": object cycles down a list of fixed receptacles
2. "fixed_0.1_0.9": object has 10% chance of staying put, 90% chance of going to the next receptacle in cycle  (this is what the 2D flowmaps simulator has)
3. "uniform_no_diag": fully uniform transition matrix
4. "uniform_full": fully uniform transition matrix
5. "location_weighted_uniform_no_diag": uniform transition matrix weighted by the ProcThor receptacle prior
6. "location_weighted_uniform_full": uniform transition matrix weighted by the ProcThor receptacle prior

### Preliminary scan experiments

 1. SCANSIZE 10: ~33.5 it/s : 335 steps/s
2. 100 : 33 : 3300


1000 : eta 50min

1000 : cpu: 3s/it; cuda is same!

# To build a package for PyPi

```bash
# bump the version in the .toml

uv build

# delete the old build in ./dist

uv publish
```
