import os
import shlex
import sys

from hydra.core.hydra_config import HydraConfig
import subprocess

def maybe_spoof_hydra(py_file):
    if "HYDRA_SPOOF" in os.environ and os.environ["HYDRA_SPOOF"] == "toplevel":
        print("Detected HYDRA_SPOOF environment variable. Launching bottom-level code now...")

        hc = HydraConfig.get()
        overrides = hc.overrides.task
        print("Overrides passed to toplevel:")
        print(overrides)
        curpath = os.getcwd()
        print(f"Current path: {curpath}")
        print("Launching bottom-level hydra subprocess...")
        print(os.environ.get("CUDA_VISIBLE_DEVICES", "NOPE"))


        clean_env = {
            'HOME': os.environ['HOME'],
            'USER': os.environ['USER'],
            'LOGNAME': os.environ.get('LOGNAME', os.environ['USER']),
            'TERM': os.environ.get('TERM', 'xterm-256color'), # Helpful for output formatting
            'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
            # 'PATH': '/usr/bin:/bin' # Optional: Safety net if login scripts are broken
        }

        # 2. Construct your command string
        # Note: I uncommented the conda hook. It is safer than relying on .bashrc
        # because .bashrc often has "return if not interactive" guards at the top.
        conda_exe = "$HOME/miniconda3/bin/conda"
        cmd_str = (
            'module unload python/3.10 || true && ' # || true prevents crash if module not found
            f'eval "$({conda_exe} shell.bash hook)" && '
            'conda activate sss && '
            f'cd "{curpath}" && '
            f'HYDRA_SPOOF="bottomlevel" TQDM_DISABLE=1 XLA_PYTHON_CLIENT_PREALLOCATE=false JAX_PLATFORM_NAME=cpu APPEND_CONDA_TO_LD_LIBRARY_PATH=True '
            f'uv run -m {py_file} {shlex.join(overrides)}'
        )

        print(f"Running raw command: {cmd_str}")

        # 3. Run with /bin/bash -l -c
        # We use shell=False so we can pass the '-l' flag explicitly to the executable.
        result = subprocess.run(
            ['/bin/bash', '-l', '-c', cmd_str],
            shell=False,
            check=False,  # Changed to False so it doesn't raise an exception on error
            env=clean_env
        )

        # Exit with the exact code returned by the subprocess
        sys.exit(result.returncode)
    elif "HYDRA_SPOOF" in os.environ and os.environ["HYDRA_SPOOF"] == "bottomlevel":
        print("Detected HYDRA_SPOOF environment variable set to bottomlevel.")
        print("Attempting to import jax...")
        import jax.numpy as jnp
        jnp.ones(10) * jnp.ones(10) * 2
        print("Success. Launching main implementation...")
