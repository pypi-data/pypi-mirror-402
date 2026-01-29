import copy
import shutil
import os
import sys

from semistaticsim.spoof_hydra import maybe_spoof_hydra

os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
import functools
import numpy as np
import hydra
import json
import os
from tqdm import tqdm, trange
import tempfile
from omegaconf import OmegaConf

if not OmegaConf.has_resolver("eval"):
    OmegaConf.register_new_resolver("eval", eval)

def to_serializable(obj):
    import jax
    jax.config.update('jax_platform_name', "cpu")
    import jax.numpy as jnp

    """Recursively convert JAX or NumPy arrays to Python types."""
    if isinstance(obj, (jnp.ndarray, np.ndarray)):
        return obj.item()
    elif hasattr(obj, "item") and callable(obj.item):
        # scalar array
        try:
            return obj.item()
        except Exception:
            return float(obj)
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_serializable(v) for v in obj]
    else:
        return obj


def _main_impl(cfg):
    from semistaticsim.datawrangling.sssd import thin2wide
    from semistaticsim.groundtruth import schedule_generation
    from semistaticsim.groundtruth.objects import ObjectCollection
    from semistaticsim.groundtruth.procthor_object import ProcThorObject
    from semistaticsim.groundtruth.sim import Simulator
    from semistaticsim.groundtruth.utils import seed_everything
    from semistaticsim.groundtruth.schedule import Schedule, TIME_SCALES_MAPPING
    from semistaticsim.groundtruth.spoof_vmap import spoof_vmap
    import jax
    #jax.config.update('jax_platform_name', "cpu")
    import jax.numpy as jnp
    import polars as pl


    bare_cfg = copy.copy(cfg)

    print("Setting schedule generation function...")
    schedule_generation_func = functools.partial(schedule_generation.full_pattern, **cfg.schedule)

    # Add seed with procthor index to have different data per process
    seed = cfg.seed + cfg.procthor_index 
    print(f"Seeding everything with {seed}...")
    key = seed_everything(seed)
    key, rng = jax.random.split(key)
    print("Loading object collection...")
    object_collection: ObjectCollection = hydra.utils.call(cfg.objects, key=rng)

    print("Generating schedules...")
    schedules = []
    for i, object in enumerate(tqdm(object_collection.pickupable_to_receptacles.keys())):
        location_indices = object_collection.valid_receptacle_indices_for_pickupable_index(i)
        location_weights = object_collection.mat_pickupable_to_receptacles[i,location_indices]
        num_pad_locations = object_collection.mat_pickupable_to_receptacles.shape[1] - len(location_indices)
        location_indices = np.array(location_indices).tolist()

        key, rng = jax.random.split(key)
        schedule_pattern =  schedule_generation_func(
                key=rng,
                locations=location_indices,
                locations_weights=location_weights,
                num_pad_locations=num_pad_locations,
                dt=cfg.dt
            )

        location_names = [object_collection.receptacle_index_to_id(i) for i in location_indices]

        key, rng = jax.random.split(key)
        schedule = Schedule.create(rng, schedule_pattern, scales=cfg.schedule.scales, locations= location_indices + [-1] * num_pad_locations, dt=cfg.dt)
        schedules.append(schedule)

    print("Creating simulator...")
    schedules = spoof_vmap(schedules)
    simulator = Simulator.create(key=jax.random.PRNGKey(0), object_collection=object_collection, schedule=schedules)

    #simulator = simulator.step(key=jax.random.PRNGKey(0))

    timespan = cfg.timespan_to_collect
    num, unit = timespan.split()
    num = int(num)
    unit = TIME_SCALES_MAPPING[unit]
    timespan = num * unit * (1 / simulator.schedule.dt[0])
    num_of_scans_to_do = timespan // cfg.jax_scan_size
    if num_of_scans_to_do * simulator.schedule.dt[0] < timespan:
        num_of_scans_to_do += 1

    print("Number of time to get:", cfg.timespan_to_collect)
    print("Number of time in terms of units:", num * unit)
    del num
    del unit
    print("Current dt:", simulator.schedule.dt[0])
    print("Number of dt we need to fill timespan to collect:", timespan)
    print(f"Number of scans to do with scansize {cfg.jax_scan_size}:", num_of_scans_to_do)

    #with jax.disable_jit():
    thunk = simulator.make_scan_thunk(cfg.jax_scan_size, cfg.jax_scan_unroll)

    # create a temporary directory under /tmp
    tmpdir = tempfile.mkdtemp(dir="/tmp")

    with open(os.path.join(tmpdir, "pickupable_to_receptacle.json"), 'w') as f:
        pickupable_to_receptacles = {}
        for pickupable_id, row in enumerate(simulator.object_collection.mat_pickupable_to_receptacles):
            pickupable_to_receptacles[simulator.pickupable_names[pickupable_id]] = [simulator.receptacle_names[i] for i in np.array(jnp.nonzero(row > 0)).tolist()[0]]
        json.dump(pickupable_to_receptacles, f, indent=4)

    # Save receptacles' pose
    receptacles_oobb = {}
    for id, receptacle in enumerate(simulator.receptacle_names):
        obj_metadata = simulator.object_collection.get_receptacle_by_index(id)
        oobb = obj_metadata.get_oobb()
        receptacles_oobb[receptacle] = to_serializable(oobb)
        
    with open(os.path.join(tmpdir, "receptacles_oobb.json"), 'w') as f:
        json.dump(receptacles_oobb, f, indent=4)

    with open(os.path.join(tmpdir, "receptacle_names.json"), 'w') as f:
        json.dump(simulator.receptacle_names, f, indent=4)

    with open(os.path.join(tmpdir, "pickupable_names.json"), 'w') as f:
        json.dump(simulator.pickupable_names, f, indent=4)

    for step in trange(int(num_of_scans_to_do)):
        key, rng = jax.random.split(key)
        simulator, data = thunk(key, simulator)
        timestamps = (jnp.arange(cfg.jax_scan_size) + step * cfg.jax_scan_size) * simulator.schedule.dt[0]
        data['timestamp'] = timestamps[:, jnp.newaxis]
        data["assignment"] = thin2wide(data["assignment"], simulator.receptacle_names)

        if cfg.output_bboxes:
            aabb, oobb = jax.vmap(ProcThorObject.resolve_bboxes, in_axes=(0,1,1))(simulator.object_collection.pickupables, data["position"], data["rotation"])
            data["aabb_center"] = aabb["center"].transpose(1,0,2)
            data["aabb_cornerPoints"] = aabb["cornerPoints"].transpose(1,0,2,3)
            data["aabb_size"] = aabb["center"].transpose(1,0,2) # jnp.concatenate((aabb["size"]["x"][None], aabb["size"]["y"][None], aabb["size"]["z"][None])).transpose(2,1,0)
            data["oobb_cornerPoints"] = oobb["cornerPoints"].transpose(1,0,2,3)

        data = {k:np.array(v) for k,v in data.items()}

        data = pl.DataFrame(data)

        out_path = os.path.join(tmpdir, f"scan_{step}.parquet")
        data.write_parquet(out_path)

    print(f"Dumped data to <{tmpdir}>, now moving it to <{cfg.target_dir}>")
    # Delete existing results
    if os.path.exists(cfg.target_dir):
        shutil.rmtree(cfg.target_dir)
    os.makedirs(cfg.target_dir, exist_ok=True)

    for filename in os.listdir(tmpdir):
        src_path = os.path.join(tmpdir, filename)
        dst_path = os.path.join(cfg.target_dir, filename)
        shutil.move(src_path, dst_path)
    with open(cfg.target_dir + "/config.yaml", "w") as f:
        OmegaConf.save(cfg, f, resolve=False)


@hydra.main(version_base=None, config_path="config", config_name="config")
def cli_main(cfg):
    maybe_spoof_hydra("semistaticsim.groundtruth.main")

    return _main_impl(cfg)

def main(version_base=None, config_path=None, config_name="config", overrides=None):
    # Use absolute path to config directory for package compatibility
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config")
    from hydra import initialize_config_dir, compose
    from hydra.core.hydra_config import HydraConfig

    if overrides is None:
        overrides = []

    with initialize_config_dir(
        config_dir=config_path,
        version_base=None,
    ):
        cfg = compose(
            config_name=config_name,
            overrides=overrides,
            return_hydra_config=True
        )
        HydraConfig.instance().set_config(cfg)
    return _main_impl(cfg)

if __name__ == "__main__":
    cli_main()
