from pprint import pprint as pp
import json

NAMELIST = [
    ### PWscf
    # pw.x & cp.x 
    "control", "system", "electrons", "ions", "cell", "fcp", "rism",

    # hp.x
    "inputhp",

    # bgw2pw.x
    "input_bgw2pw",

    # pw2bgw.x
    "input_pw2bgw",

    # pwcond.x 
    "inputcond",

    # pprism.x
    "inputpp", # & cppp.x 
    "plot",

    # oscdft_et.x 
    "oscdft_et_namelist",

    ### PHonon
    # ph.x 
    "inputph",

    # dynmat.x & matdyn.x & postahc.x & q2r.x & d3hess.x 
    "input",

    ### atomic, ld1.x
    "input", "inputp", "test",

    ### KCW, kcw.x 
    "control", "wannier", "screen", "ham",

    ### --- POST PROCESS ---
    # pp.x
    "inputpp", # pw2wannier90.x 
    "plot",
    # dos.x
    "dos",
    # bands.x 
    "bands",
    # band_interpolation.x
    "interpolation",
    # projwfc.x
    "projwfc",
    # molecularpdos.x 
    "inputmopdos",
    # ppp.x
    "inputpp",
    # ppacf.x
    "ppacf",
    # oscdft_pp.x
    "oscdft_pp_namelist",
]

## constraint: PWneb, XSpectra, QEHeat
## importexport_binary.x, 

def get_data(path, validation=True, get_project_path=False):
    with open(path, "r") as f:
        data = json.load(f)

    project_path = prepare_path_workingspace(data['main'])
    if validation:
        data = valid_pp_path(data, path)

    if not get_project_path:
        return data
    return data, project_path

def item_str(items: dict | list | str):
    text = ""
    if isinstance(items, dict):
        for k, v in items.items():
            

            if isinstance(v, str) and v.startswith('$script'):
                v = get_return_config(v)
                if isinstance(v, bool):
                    v = f".{v}.".lower()
                text += f"   {k} = {v}\n"
            elif isinstance(v, bool):
                v = f".{v}.".lower()
                text += f"   {k} = {v}\n"
            else:
                text += f"   {k} = {v if not isinstance(v, str) else f"\'{v}\'"}\n"
    elif isinstance(items, list):
        for v in items:
            if isinstance(v, bool):
                v = f".{v}.".lower()
            text += f"   {v}\n"
    else:
        text += f"   {items}\n"

    return text

def split_opt(text: str):
    text = text.split("(")
    if len(text) == 1:
        return text[0], None
    return text[0].strip(), f"({text[1].strip()}"



def get_default(default: dict):
    script = ""
    for key, item in default.items():
        
        card, opt = split_opt(key)
        if card.strip() in NAMELIST:
            
            script += f"&{card.upper()} {opt if opt is not None else ""}\n"
            script += item_str(item) + "/"

        else:
            script += f"{card.upper()} {opt if opt is not None else ""}\n"
            script += item_str(item)
        script += "\n\n"
    return script

def get_original(original: dict):
    script = ""
    for key, item in original.items():
        
        card, opt = split_opt(key)
        if card.strip() in NAMELIST:
            
            script += f"&{card.upper()} {opt if opt is not None else ""}\n"
            script += item_str(item) + "/"

        else:
            script += f"{card.upper()} {opt if opt is not None else ""}\n"
            script += item_str(item)
        script += "\n\n"
    return script

def get_replace_default_str(default: dict, replace: dict):

    namelist_dict = {}
    other_dict = {}

    for k, v in default.items():
        base_k, _ = split_opt(k)
        if k in NAMELIST:
            if k not in namelist_dict:
                namelist_dict[k] = v
                continue

            for sub_k, sub_v in v.items():
                namelist_dict[k][sub_k] = sub_v
        else:
            other_dict[k] = v

    for k, v in replace.items():
        base_k, _ = split_opt(k)
        if k in NAMELIST:
            if k not in namelist_dict:
                namelist_dict[k] = v
                continue

            for sub_k, sub_v in v.items():
                namelist_dict[k][sub_k] = sub_v
        else:
            other_dict[k] = v

    default = {**namelist_dict, **other_dict}

    for k, v in replace.items():
        base_k, _ = split_opt(k)

        if isinstance(v, str) and v.startswith("$script"):
            v = get_return_config(v)

        if base_k in NAMELIST:
            if isinstance(v, bool):
                v = f".{v}."
            if isinstance(v, dict):
                for i, el in v.items():
                    if isinstance(el, str) and el.startswith("$script"):
                       v[i] =  get_return_config(el)
                default[k] = default.get(k, {}) | v
            else:
                default[k] = v

        else:
            keys_to_remove = [dk for dk in default if split_opt(dk)[0] == base_k]
            for dk in keys_to_remove:
                default.pop(dk)
            if isinstance(v, bool):
                v = f".{v}."
            default[k] = v

    script = get_default(default)
    return script

def get_replace_default_json(default: dict, replace: dict):

    for k, v in replace.items():
        base_k, _ = split_opt(k)

        if isinstance(v, str) and v.startswith("$script"):
            v = get_return_config(v)

        if base_k in NAMELIST:
            if isinstance(v, dict):
                for i, el in v.items():
                    if isinstance(el, str) and el.startswith("$script"):
                       v[i] =  get_return_config(el)
                default[k] = default.get(k, {}) | v
            else:
                default[k] = v

        else:
            keys_to_remove = [dk for dk in default if split_opt(dk)[0] == base_k]
            for dk in keys_to_remove:
                default.pop(dk)
            
            default[k] = v

    return default

import pathlib

def prepare_path_workingspace(base: dict):
    project_dir = pathlib.Path(base['project_dir'])
    current_dir = pathlib.Path.cwd()
    project_path = current_dir/project_dir
    project_path.mkdir(parents=True, exist_ok=True)
    return project_path


def valid_pp_path(data: dict, json_path: pathlib.Path):

    assert 'pseudo_dir' in data['main'].keys(), "pseudo_dir is missing in config"
    
    if pathlib.Path(data['main']["pseudo_dir"]).is_absolute():
        pp_path = pathlib.Path(data['main']["pseudo_dir"]).resolve()
        data['default']['control']['pseudo_dir'] = str(pp_path)
        return data
    
    
    json_dir = pathlib.Path(json_path).parent
    pp_path = (json_dir / pathlib.Path(data['main']["pseudo_dir"])).resolve()

    data['default']['control']['pseudo_dir'] = str(pp_path)

    return data

import subprocess
import importlib

def get_return_config(import_str: str): 
    """
    import_str like "$script script.test_module:get_one_two_three"
    """

    import_str = import_str.split("$script")[-1].strip()
    module, function = import_str.split(":")

    str_module = importlib.import_module(module)

    return getattr(str_module, function)()



def process(json_path: str) -> dict:

    data, project_path = get_data(json_path, get_project_path=True) 

    pending = {}

    default = data['default'].copy()
    
    default_script = get_default(default)

    pending['default'] = { "path": project_path / "default", "script": default_script }

    for key, run in data.items():
        if key == "main" or key == "default":
            continue

        if isinstance(run, dict):
            default = data['default'].copy()
            script = get_replace_default_str(default, run)
            pending[key] = { "path": project_path / key, "script": script }

        elif isinstance(run, list):
            for idx, sub_val in enumerate(run):
                default = data['default'].copy()
                
                script = get_replace_default_str(default, sub_val)
                
                pending[f"{key}-{idx}"] = { "path": project_path / f"{key}-{idx}", "script": script }

    return pending

def process_pending_json(json_path: str) -> dict:

    data, project_path = get_data(json_path, get_project_path=True) 

    pending = {}

    default = data['default'].copy()
    
    pending['default'] = { "path": project_path / "default", "script": data['default'] }

    for key, run in data.items():
        if key == "main" or key == "default":
            continue

        if isinstance(run, dict):
            default = data['default'].copy()
            script_json = get_replace_default_json(default, run)
            pending[key] = { "path": project_path / key, "script": script_json }

        elif isinstance(run, list):
            for idx, sub_val in enumerate(run):
                default = data['default'].copy()

                script_json = get_replace_default_json(default, sub_val)
                
                pending[f"{key}-{idx}"] = { "path": project_path / f"{key}-{idx}", "script": script_json }

    return pending

def process_at_runtime(json_path: str) -> dict:

    data, project_path = get_data(json_path, get_project_path=True) 

    pending = {}

    pending['default'] = { "path": project_path / "default", "script": data['default'] }

    for key, run in data.items():
        if key == "main" or key == "default":
            continue

        if isinstance(run, dict):
            pending[key] = { "path": project_path / key, "script": run }

        elif isinstance(run, list):
            for idx, sub_val in enumerate(run):
                pending[f"{key}-{idx}"] = { "path": project_path / f"{key}-{idx}", "script": sub_val }

    return pending

def run_qe(job_id, input_file, output_file, n_proc = 4, wait=True, binary_map="pw.x"):

    cmd = f"mpirun -np {n_proc} {binary_map} -in {input_file} > {output_file}"
    
    print(f"🚀 Running job id: {job_id}\n🫱  At path: {input_file} ...", end="", flush=True)
    
    if wait:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(" [DONE]")
            with open(output_file, 'r') as f:
                lines = f.readlines()
                last_lines = "".join(lines[-20:])
                if "JOB DONE" in last_lines:
                    print(f"✅ job id {job_id} Converged!\n")
                    return True
                else:
                    print(f"❌ job id {job_id} failed to converge.\n")
                    return False
        else:
            print(" 💥 Crash!")
            print(result.stderr)
            return False
    else:
        result = subprocess.Popen(cmd, shell=True)
        print("✅ Calculation start!")


def write_file(job_id: str, job_data: dict):

    pathlib.Path.mkdir(job_data['path'], parents=True, exist_ok=True)

    with open(job_data['path'] / f"{job_id}.in", "w") as f:
        f.write(job_data['script'])

def write_from_json_script(job_id: str, job_data: dict):

    script = get_default(job_data["script"])

    pathlib.Path.mkdir(job_data['path'], parents=True, exist_ok=True)

    with open(job_data['path'] / f"{job_id}.in", "w") as f:
        f.write(script)

import shutil

def write_from_json_script_at_runtime(
    job_id: str, 
    job_data: dict, 
    default: dict | None, 
    key_to_cp: str | None,
):
    
    if default is not None:
        script = get_replace_default_str(default, job_data['script'])
    else:
        script = get_original(job_data['script'])

    if key_to_cp is not None:
        
        try:
            source_path = (job_data['path'] / ".." / key_to_cp).resolve()
            shutil.copytree(source_path, job_data['path'])
            print(f"🫨  Continue from '{key_to_cp}' as path '{job_data['path']}'")

            
        except FileExistsError:
            print(f"😥 [Error] Destination directory '{job_data['path']}' already exists, \n💫 Script {job_id}.in is created anyway!")
        except OSError as e:
            print(f"😥 [Error] {e}")
        
        with open(job_data['path'] / f"{job_id}.in", "w") as f:
            f.write(script)
    else:

        pathlib.Path.mkdir(job_data['path'], parents=True, exist_ok=True)

        with open(job_data['path'] / f"{job_id}.in", "w") as f:
            f.write(script)

import os

def start_simulating(json_path: str, run=True):
    import time

    start_time = time.time()
    data = get_data(json_path)
    meta = data['main']

    assert not ("exclude_keys" in meta.keys() and "include_keys" in meta.keys()), "😔 `exclude_keys` and `include_keys` can't be specified at the same time"
    n_proc = meta['n_proc'] if "n_proc" in meta.keys() else 4
    binary_default = meta['binary_default'] if 'binary_default' in meta.keys() else "pw.x"
    job_bins = meta['binary_map'] if 'binary_map' in meta.keys() else None

    use_checkpoint = meta['use_checkpoint'] if "use_checkpoint" in meta.keys() else {}
    key_to_prevent_default = meta['prevent_default'] if "prevent_default" in meta.keys() else []

    pending = process_at_runtime(json_path) 

    start_at_key = meta['start_at_key'] if "start_at_key" in meta.keys() else \
        f"{list(data.keys())[2]}-0" if len(data.keys()) > 2 and isinstance(data[list(data.keys())[2]], list) else \
            list(data.keys())[2] if len(data.keys()) > 2 else "default"

    except_job = meta['exclude_keys'] if "exclude_keys" in meta.keys() else []
    include_keys = meta['include_keys'] if "include_keys" in meta.keys() else pending.keys()

    start = False

    for job_id, job_data in pending.items():

        if job_id == start_at_key:
            start = True

        if not start:
            print(f"🫠  [SKIP] job id: {job_id}...\n")
            continue

        if job_id in except_job or job_id not in include_keys:
            print(f"🫠  [SKIP] job id: {job_id}... since either not include_keys or in exception\n")
            continue
        
        job_bin = None
        if job_bins is not None and job_id in job_bins:
            job_bin = job_bins[job_id]

        key_to_cp = use_checkpoint[job_id] if job_id in use_checkpoint else None
        
        write_from_json_script_at_runtime(
            job_id, job_data, 
            default=data['default'].copy() if job_id not in key_to_prevent_default else None, 
            key_to_cp=key_to_cp
        )

        if run:
            current_dir = os.curdir
            os.chdir(job_data['path'])
            run_qe(
                job_id,
                job_data['path'] / f"{job_id}.in", 
                job_data['path'] / f"{job_id}.out", 
                n_proc,
                binary_map=job_bin if job_bin is not None else binary_default
            )
            os.chdir(current_dir)


    print(f"🫡  [DONE] total time usage... {time.time() - start_time:.3f}s")


# start_simulating("config/mg2feh6.json")

from scriptation.preprocessor import Preprocessor
from scriptation.scheduler import Scheduler
from scriptation.executor import Executor

import logging

logging.basicConfig(level=logging.INFO)
    
preprocessor = Preprocessor("/home/shinapri/Documents/quantum-espresso/scriptation-2/config/qe.json")
scheduler = Scheduler(preprocessor)

executor = Executor()


# import time
# start_time = time.time()
# executor.execute_batch(scheduler)
# print(f"\n\n     🫡  [FINISH] total time usage... {time.time() - start_time:.3f}s")




# pp(process_at_runtime("test/qe.json"))

# import spglib
# from ase import Atoms
# from ase.io import read


# atoms = read('/home/shinapri/Documents/quantum-espresso/scriptation-2/mg2feh6/Mg2FeH6.poscar')

# lattice, scaled_pos, numbers = spglib.standardize_cell(
#     (atoms.get_cell(), atoms.get_scaled_positions(), atoms.get_atomic_numbers()), 
#     to_primitive=True, 
#     symprec=1e-5
# )

# # 3. สร้าง Atoms object ใหม่ที่เป็น 9 อะตอม
# primitive_atoms = Atoms(
#     numbers=numbers, 
#     cell=lattice, 
#     scaled_positions=scaled_pos, 
#     pbc=True
# )

# # ดูพิกัดแบบ Crystal (Scaled)
# print("--- ATOMIC_POSITIONS (crystal) ---")
# for sym, pos in zip(primitive_atoms.get_chemical_symbols(), primitive_atoms.get_scaled_positions()):
#     print(f"{sym} {pos[0]:.10f} {pos[1]:.10f} {pos[2]:.10f}")

# # ดู Cell Parameters (เพื่อเอาไปใส่ ibrav=0 หรือคำนวณ celldm)
# print("\n--- CELL_PARAMETERS (angstrom) ---")
# for vector in primitive_atoms.get_cell():
#     print(f"{vector[0]:.10f} {vector[1]:.10f} {vector[2]:.10f}")