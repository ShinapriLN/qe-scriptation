

from scriptation.preprocessor import Preprocessor
from scriptation.scheduler import Scheduler

import logging
from pprint import pprint as pp
import subprocess
import importlib
from pathlib import Path
import shutil
import os
import multiprocessing
import time

logger = logging.getLogger(__name__)


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


class Executor:

    def evaluate(self):
        pass

    def get_default(self, default: dict):
        script = ""
        for key, item in default.items():
            
            card, opt = self.split_opt(key)
            if card.strip() in NAMELIST:
                
                script += f"&{card.upper()} {opt if opt is not None else ""}\n"
                script += self.item_str(item) + "/"

            else:
                script += f"{card.upper()} {opt if opt is not None else ""}\n"
                script += self.item_str(item)
            script += "\n\n"


        return script

    def get_eval_script(self, import_str: str): 
        """
        import_str like "$script script.test_module:get_one_two_three"
        """

        import_str = import_str.split("$script")[-1].strip()
        module, function = import_str.split(":")

        str_module = importlib.import_module(module)

        return getattr(str_module, function)()

    def item_str(self, items: dict | list | str):
        text = ""
        if isinstance(items, dict):
            for k, v in items.items():
                

                if isinstance(v, str) and v.startswith('$script'):
                    v = self.get_eval_script(v)
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

    def split_opt(self, text: str):
        text = text.split("(")
        if len(text) == 1:
            return text[0], None
        return text[0].strip(), f"({text[1].strip()}"

    def get_original_script(self, original: dict):
        script = ""
        for key, item in original.items():
            
            card, opt = self.split_opt(key)
            if card.strip() in NAMELIST:
                
                script += f"&{card.upper()} {opt if opt is not None else ""}\n"
                script += self.item_str(item) + "/"

            else:
                script += f"{card.upper()} {opt if opt is not None else ""}\n"
                script += self.item_str(item)
            script += "\n\n"
        return script

    def get_merged_script(self, default: dict, replace: dict):

        namelist_dict = {}
        other_dict = {}



        for k, v in default.items():
            base_k, _ = self.split_opt(k)
            if k in NAMELIST:
                if k not in namelist_dict:
                    namelist_dict[k] = v
                    continue

                for sub_k, sub_v in v.items():
                    namelist_dict[k][sub_k] = sub_v
            else:
                other_dict[k] = v

        for k, v in replace.items():
            base_k, _ = self.split_opt(k)
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
            base_k, _ = self.split_opt(k)

            if isinstance(v, str) and v.startswith("$script"):
                v = self.get_eval_script(v)

            if base_k in NAMELIST:
                if isinstance(v, bool):
                    v = f".{v}."
                if isinstance(v, dict):
                    for i, el in v.items():
                        if isinstance(el, str) and el.startswith("$script"):
                            v[i] =  self.get_eval_script(el)
                    default[k] = default.get(k, {}) | v
                else:
                    default[k] = v

            else:
                keys_to_remove = [dk for dk in default if self.split_opt(dk)[0] == base_k]
                for dk in keys_to_remove:
                    default.pop(dk)
                if isinstance(v, bool):
                    v = f".{v}."
                default[k] = v

        script = self.get_default(default)


        return script
    
    def setup_workspace(
        self,
        job_id: str, 
        job_data: dict, 
        default: dict | None, 
        key_to_cp: str | None,
    ):  
        
    
        if default is not None:
            script = self.get_merged_script(default, job_data['script'])
        else:
            script = self.get_original_script(job_data['script'])

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

            Path.mkdir(job_data['path'], parents=True, exist_ok=True)

            with open(job_data['path'] / f"{job_id}.in", "w") as f:
                f.write(script)
    
    def execute(
        self,
        job_id, 
        n_proc, 
        binary_map,
    ):
        current_dir = Path(os.getcwd())
        input_file = current_dir / f"{job_id}.in"
        output_file = current_dir / f"{job_id}.out"

        print(f"\n[{job_id}] 🚀 Running\n[{job_id}] 👉 At path: {input_file}...", flush=True)

        cmd = f"mpirun -np {n_proc} {binary_map} -in {input_file} > {output_file}"
    
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[{job_id}] Done.")
            with open(output_file, 'r') as f:
                lines = f.readlines()
                last_lines = "".join(lines[-20:])
                if "JOB DONE" in last_lines:
                    print(f"[{job_id}] ✅ Converged!\n")
                    return True
                else:
                    print(f"[{job_id}] ❌ failed to converge.\n")
                    return False
        else:
            print(f"[{job_id}] 💥 Crash!")
            print(result.stderr)
            return False
    
    def process(
        self, 
        job_id: str, 
        job_data: dict, 
        default_script: dict, 
        config: dict
    ):

        binary_default = config['binary_default']
        n_proc = config['n_proc']
        job_bin = config['binary_map'].get(job_id, None)

        self.setup_workspace(
            job_id=job_id,
            job_data=job_data,
            default=default_script if job_id not in config.get('prevent_default', {}) else None,
            key_to_cp=config['checkpoint_map'][job_id] if "checkpoint_map" in config and job_id in config['checkpoint_map'] else None 
        )

        current_dir = os.curdir
        os.chdir(job_data['path'])
        self.execute(
            job_id,
            n_proc,
            binary_map=job_bin if job_bin is not None else binary_default
        )
        os.chdir(current_dir)
    
    def execute_batch(self, scheduler: Scheduler):
        config = scheduler.get_config()
        pending = scheduler.get_pending()
        default_script = pending["default"]

        batches = scheduler.get_schedule()
        n_batches = scheduler.get_num_schedule()

        for i in range(n_batches):

            data = [
                (
                    batches[i][j],
                    pending[batches[i][j]],
                    default_script['script'],
                    config 
                )
                for j in range(len(batches[i]))
            ]

            with multiprocessing.Pool(processes=config['max_parallel']) as pool:

                pool.starmap(self.process, data)


        
