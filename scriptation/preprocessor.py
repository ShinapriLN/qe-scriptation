

import json

from pathlib import Path
import logging
from pprint import pprint as pp

logger = logging.getLogger(__name__)

class Preprocessor:
    def __init__(self, json_path):
        with open(json_path, "r") as f:
            data = json.load(f)

        data = self.valid_pp_path(data, json_path)
        self.raw = data
        self.config, data = self.set_default_config(data)

        # mkdir of the project
        Path(self.config['project_dir']).mkdir(parents=True, exist_ok=True)

        self.pending = self.get_preprocess(self.config, data=data)
    
    def get_preprocess(self, config, data):

        pending = {
                "default": {
                "path": Path(config['project_dir']) / "default", 
                "script": data['default']
            }
        }

        for key, run in data.items():

            if isinstance(run, dict):
                pending.update(
                    {
                        key: {
                            "path": Path(config['project_dir']) / key, 
                            "script": run
                        }
                    }
                )

            elif isinstance(run, list):
                for idx, sub_val in enumerate(run):
                    job_id = f"{key}-{idx}"
                    pending.update(
                        {
                            job_id: {
                                "path": Path(config['project_dir']) / job_id, 
                                "script": sub_val
                            }
                        }
                    )
        
        pending = self.preprocess_space(pending)

        return pending
    
    def preprocess_space(self, pending: dict):
        space = self.config.get("space", None)

        if space is None:
            return pending
        
        for sp in space:
            pending = getattr(self, f"preprocess_{sp}")(pending)

        return pending
    

    def preprocess_stress_strain(self, pending):
        stress_strain_config = self.config['space']['stress_strain']

        for ss in stress_strain_config:
            key = ss['key']
            delta = ss['delta']

            data = pending[key]
            key_idx = list(pending).index(key)

            pending.pop(key)

            pending = list(pending.items())
            for d in delta:
                data['space'] = { "delta":  d}
                for i in range(6):
                    pending.insert(key_idx, ( f"{key}-[{d}]-{i}", data ))

            pending = dict(pending)

        return pending


    def valid_pp_path(self, data: dict, json_path: Path):

        assert 'pseudo_dir' in data['config'].keys(), "pseudo_dir is missing in config"
        
        if Path(data['config']["pseudo_dir"]).is_absolute():
            pp_path = Path(data['config']["pseudo_dir"]).resolve()
            data['default']['control']['pseudo_dir'] = str(pp_path)
            return data
        
        
        json_dir = Path(json_path).parent
        pp_path = (json_dir / Path(data['config']["pseudo_dir"])).resolve()

        data['default']['control']['pseudo_dir'] = str(pp_path)

        return data

    def is_key_list(self, key):
        if key in self.raw and isinstance(self.raw[key], list):
            return True
        return False


    def set_default_config(self, data: dict):

        config = data.pop("config")

        assert 'project_dir' in config, "😔 `project_dir` is missing in config."
        assert 'pseudo_dir' in config, "😔 `pseudo_dir` is missing in config."
        assert not ("exclude_keys" in config.keys() and "include_keys" in config.keys()), \
            "😔 `exclude_keys` and `include_keys` can't be specified at the same time"

        if "n_proc" not in config:
            logger.info("\n\n     😎 `n_proc` was not set -> use default '4'.\n")
            config['n_proc'] = 4

        if "max_parallel" not in config:
            logger.info("\n\n     😎 `max_parallel` was not set, use default '1'.\n")
            config['max_parallel'] = 1

        if "binary_default" not in config:
            logger.info("\n\n     😎 `binary_default` was not set -> use default 'pw.x'.\n")
            config['binary_default'] = 'pw.x'

        if "binary_map" not in config:
            logger.info(f"\n\n     😎 `binary_map` were not set -> all keys use default binary_map {config['binary_default']}\n")
            config['binary_map'] = {k:config['binary_default'] for k in data.keys()}
        else:
            config['binary_map'].update({k: config['binary_default'] for k in data.keys() if k not in config['binary_map']})

        return config, data



