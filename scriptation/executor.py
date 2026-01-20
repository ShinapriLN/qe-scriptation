

from scriptation.scheduler import Scheduler
from scriptation.utils import Default, NAMELIST

import logging
import subprocess
import importlib
from pathlib import Path
import shutil
import os
import multiprocessing

logger = logging.getLogger(__name__)

class Executor:

    def dict_to_script(self, script_dict: dict):
        script = ""
        for key, item in script_dict.items():
            
            card, opt = self.split_header(key)
            if card.strip() in NAMELIST:
                
                script += f"&{card.upper()} {opt if opt is not None else ""}\n"
                script += self.dict_to_script_loop(item) + "/\n"

            else:
                script += f"{card.upper()} {opt if opt is not None else ""}\n"
                script += self.dict_to_script_loop(item)
            script += "\n"

        return script

    def evaluate(self, import_str: str): 
        """
        import_str like "$script script.test_module:get_one_two_three"
        """

        import_str = import_str.split("$script")[-1].strip()
        module, function = import_str.split(":")

        
        str_module = importlib.import_module(module)

        return getattr(str_module, function)()
    
    def get_line_format(self, value, key = None):
        if isinstance(value, str) and value.startswith('$script'):
            value = self.evaluate(value)
            if isinstance(value, bool):
                value = f".{value}.".lower()

        elif isinstance(value, bool):
            value = f".{value}.".lower()

        elif isinstance(value, str):
            value = f"\'{value}\'"

        else:
            value = f"{value}"

        if key is not None:
            return f"   {key} = {value}\n"
        return f"   {value}\n"
    
    def get_line_format_exact(self, value, key=None):
        if isinstance(value, str) and value.startswith('$script'):
            value = self.evaluate(value)
            if isinstance(value, bool):
                value = f".{value}.".lower()

        elif isinstance(value, bool):
            value = f".{value}.".lower()

        else:
            value = f"{value}"

        if key is not None:
            return f"   {key} = {value}\n"
        return f"   {value}\n"

    def dict_to_script_loop(self, items: dict | list | str):
        text = ""
        if isinstance(items, dict):
            for k, v in items.items():
                text += self.get_line_format(v, k)

        elif isinstance(items, list):
            for v in items:
                # use exact for non-namelist. exact means
                # if wrote in config as "key": "value"   -> value
                # ...                   "key": "'value'" -> 'value'
                text += self.get_line_format_exact(v)

        else:
            text += self.get_line_format_exact(items)

        return text

    def split_header(self, text: str):
        text = text.split(" ")
        if len(text) == 1:
            return text[0], None
        return text[0].strip(), text[1].strip()

    def dict_to_script_merged(self, default: dict, replace: dict):

        get_key_no_header = lambda k: self.split_header(k)[0]
        
        # remove the key in default if replacing
        # can be change from different header
        # CARD (header_1) -> CARD (header_2) so no duplicate
        replace_keys_clean = {
            get_key_no_header(k) for k in replace if get_key_no_header(k) not in NAMELIST
        }
        tmp = default.copy()
        for dk in tmp:
            dk_clean = get_key_no_header(dk)
            if dk_clean in replace_keys_clean:
                default.pop(dk)

        # find insert index in default of namelist 
        # since qe doesn't allow namelist after cards 
        for insert_idx, k in enumerate(default):
            if k not in NAMELIST:
                break
        
        tmp = default.copy()
        default = list(default.items())

        # insert the namelist if not exist
        # otherwise merged the dict
        # if it's the card, override it 
        for k, v in replace.items():
            base_k, _ = self.split_header(k)
            if base_k in NAMELIST and base_k not in tmp:
                default.insert(insert_idx, (k, v))

            elif base_k in NAMELIST and base_k in tmp:
                default = dict(default)
                default[k] = default[k] | replace[k]
                default = list(default.items())

            else:
                default.append((k, v))

        default = dict(default)
        script = self.dict_to_script(default)

        return script
    
    def setup_job_project(
        self,
        key: str, 
        data: dict, 
        default: dict | None, 
        key_to_cp: str | None,
    ):  
        
    
        if default is not None:
            script = self.dict_to_script_merged(default, data['script'])
        else:
            script = self.dict_to_script(data['script'])

        if key_to_cp is not None:
            
            try:
                source_path = (data['path'] / ".." / key_to_cp).resolve()
                shutil.copytree(source_path, data['path'])
                print(f"🫨  Continue from '{key_to_cp}' at path '{data['path']}'")

            except FileExistsError:
                print(f"😥 [Warning] Destination directory '{data['path']}' already exists, \n💫 Script {key}.in is created anyway!")

            except OSError as e:
                print(f"😥 [Error] {e}")
            
            with open(data['path'] / f"{key}.in", "w") as f:
                f.write(script)
        else:

            Path.mkdir(data['path'], parents=True, exist_ok=True)

            with open(data['path'] / f"{key}.in", "w") as f:
                f.write(script)
    
    def execute(
        self,
        key, 
        n_proc, 
        binary,
    ):
        current_dir = Path(os.getcwd())
        input_file = current_dir / f"{key}.in"
        output_file = current_dir / f"{key}.out"


        print(f"\n[{key}] 🚀 Running\n[{key}] 👉 At path: {input_file}...", flush=True)

        cmd = f"mpirun -np {n_proc} {binary} -in {input_file} > {output_file}"
    
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            with open(output_file, 'r') as f:
                lines = f.readlines()
                last_lines = "".join(lines[-20:])
                if "JOB DONE" in last_lines:
                    print(f"[{key}] ✅ Done!\n")
                    return True
                else:
                    print(f"[{key}] ❌ failed to converge.\n")
                    return False
        else:
            print(f"[{key}] 💥 Crash!")
            print(result.stderr)
            return False
    
    def process(
        self, 
        key: str, 
        data: dict, 
        default_script: dict, 
        config: dict
    ):

        binary_default = config.get("binary_default", Default.binary_default)
        n_proc = config.get("n_proc", Default.n_proc)
        job_bin = config['binary_map'].get(key, None)

        self.setup_job_project(
            key=key,
            data=data,
            default=default_script if key not in config.get('prevent_default', {}) else None,
            key_to_cp=config['use_checkpoint'][key] if "use_checkpoint" in config and key in config['use_checkpoint'] else None 
        )

        current_dir = os.curdir
        os.chdir(data['path'])
        try:
            Path(f"{key}.out").rename(f"{key}.out.old")
        except:
            ...

        self.execute(
            key,
            n_proc,
            binary=job_bin if job_bin is not None else binary_default
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


        
