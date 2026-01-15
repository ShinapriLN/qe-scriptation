from pprint import pprint as pp
import json

NAMELIST = ["control", "system", "electrons", "ions", "cell", "fcp", "rism"]

def get_data(path, validation=True, get_project_path=False):
    with open(path, "r") as f:
        data = json.load(f)

    project_path = prepare_path_workingspace(data['main'])
    if validation:
        data = valid_pp_path(data, project_path)

    if not get_project_path:
        return data
    return data, project_path

def item_str(items: dict | list | str):
    text = ""
    if isinstance(items, dict):
        for k, v in items.items():
            text += f"   {k} = {v if not isinstance(v, str) else f"\'{v}\'"}\n"
    elif isinstance(items, list):
        for v in items:
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

def get_replace_default_str(default: dict, replace: dict):

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
    project_dir = pathlib.Path(base['project-dir'])
    current_dir = pathlib.Path.cwd()
    project_path = current_dir/project_dir
    project_path.mkdir(parents=True, exist_ok=True)
    return project_path


def valid_pp_path(data: dict, project_path: pathlib.Path):

    assert 'pseudo-dir' in data['main'].keys(), "pseudo-dir is missing in config"

    pp_path = project_path / ".." / pathlib.Path(data['main']["pseudo-dir"])

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

def run_qe(job_id, input_file, output_file, n_proc = 4, wait=True):

    cmd = f"mpirun -np {n_proc} pw.x -in {input_file} > {output_file}"
    
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

def write_from_json_script_at_runtime(job_id: str, job_data: dict, default: dict):

    script = get_replace_default_str(default, job_data['script'])

    pathlib.Path.mkdir(job_data['path'], parents=True, exist_ok=True)

    with open(job_data['path'] / f"{job_id}.in", "w") as f:
        f.write(script)


def start_simulating(json_path: str, run=True):
    import time

    start_time = time.time()
    data = get_data(json_path)
    meta = data['main']

    assert not ("except" in meta.keys() and "include" in meta.keys()), "😔 `except` and `include` can't be specified at the same time"
    n_proc = meta['n_proc'] if "n_proc" in meta.keys() else 4

    pending = process_at_runtime(json_path) 

    start_at = meta['start_at'] if "start_at" in meta.keys() else list(meta.keys())[2] if len(meta.keys()) > 2 else "default"
    except_job = meta['except'] if "except" in meta.keys() else []
    include = meta['include'] if "include" in meta.keys() else pending.keys()

    start = False

    for job_id, job_data in pending.items():

        if job_id == start_at:
            start = True

        if not start:
            print(f"🫠  [SKIP] job id: {job_id}...\n")
            continue

        if job_id in except_job or job_id not in include:
            print(f"🫠  [SKIP] job id: {job_id}... since either not include or in exception\n")
            continue
        
        write_from_json_script_at_runtime(
            job_id, job_data, default=data['default'].copy()
        )

        if run:
            run_qe(
                job_id,
                job_data['path'] / f"{job_id}.in", 
                job_data['path'] / f"{job_id}.out", 
                n_proc
            )

    print(f"🫡  [DONE] total time usage... {time.time() - start_time:.3f}s")


start_simulating("test/qe.json")

# pp(process_at_runtime("test/qe.json"))

