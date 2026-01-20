

import multiprocessing
import operator


def freq(i, items: dict):
    val = list(items.values())
    curr = val[i]
    count = {}
    while True:
        if curr not in count:
            count[curr] = 1
        else:
            count[curr] += 1

        if curr in items:
            curr = items[curr]
        else:
            break
    return count


def progress_path(i, items: dict):
    keys = list(items.keys())
    curr = keys[i]
    path = []
    while True:
        path.append(curr)

        if curr in items:
            curr = items[curr]
        else:
            break
    path.reverse()
    return "->".join(path)

# test = {
#     "nscf": "scf",
#     "scf": "relax",
#     "relax": "vc-relax",
#     "vc-relax": "conv-test",
#     "conv-test": "pseudo-setup",

#     "plot_dos": "dos_calc",
#     "dos_calc": "nscf_dense",
#     "nscf_dense": "scf_converged",
#     "plot_bands": "bands_calc",
#     "bands_calc": "nscf_dense",
#     "pdos_calc": "nscf_dense",

#     "abs_spectrum": "epsilon_calc",
#     "epsilon_calc": "nscf_optical",
#     "nscf_optical": "scf_optical",
#     "scf_optical": "relax_optical",

#     "work_function": "scf_slab",
#     "scf_slab": "relax_slab",
#     "relax_slab": "init_slab",
    
#     "cleanup_tmp": "final_report",
#     "final_report": "plot_all"
# }

test = {
    "relax": "conv",
    "A": "B",
    "B": "C",
    "C": "D",
    "E": "D",
    "F": "H",
    "G": "F",
    "D": "G",
    "scf": "relax",
    "nscf": "scf"
}

with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
    
    args = [
        (i, test) for i in range(len(test))
    ]
    
    results = pool.starmap(progress_path, args)


from pprint import pprint as pp
from collections import defaultdict

# pp(results[1])

results.sort(key=len, reverse=True)

collapsed = []
big_search_pool = "" 

for path in results:
    if path not in big_search_pool:
        collapsed.append(path)
        big_search_pool += path + "|"

collapsed = [el.split("->") for el in collapsed]
pp(collapsed)