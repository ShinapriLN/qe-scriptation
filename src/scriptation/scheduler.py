

from scriptation.preprocessor import Preprocessor
from scriptation.utils import (
    draw_box, 
    split_arrow, 
    add_suffix, 
    process_path
)

import logging
from itertools import batched
import multiprocessing

logger = logging.getLogger(__name__)


class Scheduler:

    def __init__(self, data: Preprocessor):
        self.__config = data.config
        self.__pending = data.pending

        self.__seq = self.set_priority(data=data)

    def get_config(self):
        return self.__config
    
    def get_pending(self):
        return self.__pending
    
    def get_schedule(self):
        seq = [list(b) for b in self.__seq]
        return seq

    def get_num_pending(self):
        return len(self.__pending)

    def get_num_schedule(self):
        return len(self.__seq)
    
    def get_all_path(self, deps):
        
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            
            args = [
                (i, deps) for i in range(len(deps))
            ]

            results = pool.starmap(process_path, args)

            results.sort(key=len, reverse=True)


            collapsed = []
            big_search_pool = "" 

            for path in results:
                if path not in big_search_pool:
                    collapsed.append(path)
                    big_search_pool += path + "|"

            
            args = [
                (i, collapsed) for i in range(len(collapsed))
            ]
            results = pool.starmap(split_arrow, args)


        return results
    
    def valid_str_range(self, text):
        key, text = text.split("[")
        text = text.split("]")[0]
        a, b = text.split("-")
        return key.split("-")[0], int(a), int(b)

    def set_priority(self, data: Preprocessor):

        config: dict = data.config
        pending = data.pending
        pending_list = list(pending)

        max_parallel = config.get("max_parallel", 1)
        parallel_map = config.get("parallel_map", [[k] for k in data.pending.keys()])

        # set boundary from `start_at_key`, `exclude_keys` and apply to `include_keys` 
        is_start_at_key_in_config = "start_at_key" in config

        logger.info(f"\n\n     ✍️  Start Calculation From {start_at_key}\n") \
            if is_start_at_key_in_config else None
        
        start_at_key = config.get("start_at_key") if is_start_at_key_in_config \
            else f"{pending_list[1]}" if len(pending) > 1 else pending_list[0]
        
        start_at_key = start_at_key if not data.is_key_list(start_at_key) \
            else add_suffix(start_at_key, 0)
        
        start_at_idx = list(data.pending).index(start_at_key)

        exclude_jobs = config.get('exclude_keys', [])
        include_jobs = config.get(
            'include_keys', 
            [
                k for i, k in enumerate(data.pending.keys()) \
                    if i >= start_at_idx and k not in exclude_jobs
            ]
        )

        # about parallel map
        get_key_tmp = lambda k, i: f"{self.valid_str_range(k)[0]}-{i}"
        get_a_tmp = lambda k: self.valid_str_range(k)[1]
        get_b_tmp = lambda k: self.valid_str_range(k)[2] + 1
        is_condition_range = lambda k: "[" in k and "]" in k
        parallel_map = [
            [
                get_key_tmp(k, i) for k in arr if is_condition_range(k) for i in range(get_a_tmp(k), get_b_tmp(k)) 
            ] + [
                k  for k in arr if not is_condition_range(k)
            ] 
            
            for arr in parallel_map
        ]

        flatten_parallel_map = [k for b in parallel_map for k in b]

        # about other remainings
        remains = [
            [k] for k in pending \
                if k in set(flatten_parallel_map) ^ set(include_jobs)
                # not ( in flatten_parallel_map ) and ( in include_jobs )
        ] 
        
        seq = [
            *parallel_map,
            *remains
        ]

        new_seq = []
        for arr in seq:
            if not isinstance(arr, list):
                continue
            if len(arr) < max_parallel:
                new_seq.append(arr)
            else:
                new_seq.extend(list(batched(arr, max_parallel)))
        seq = [list(b) for b in new_seq]

        logger.info(f"\n\n     🫡 Calculation Schedule (max_parallel={max_parallel})\n")
        for i, b in enumerate(seq):
            num = f"({i+1}) "
            display_text = draw_box(str(", ".join(b)))
            display_text = display_text.splitlines()
            display_text = [
                " "*len(num) + row  \
                    if idx != len(display_text) // 2 \
                        else num + row \
                            for idx, row in enumerate(display_text)
            ]
            print("\n".join(display_text))

        return seq

    
    # def has_loop(self, deps: dict):
    #     for key in deps:
    #         path = []
    #         curr = key
    #         while curr in deps:
    #             if curr in path:
    #                 # logger.error(f"\nloop dependencies found.\n")
    #                 return f"{" -> ".join(path)} -> {curr}"
    #             path.append(curr)
    #             curr = deps[curr]

    #     return False
        


