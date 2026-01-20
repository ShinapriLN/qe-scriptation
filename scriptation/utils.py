

from dataclasses import dataclass

@dataclass
class Default:
    n_proc: int = 4
    max_parallel: int = 1
    binary_default: str = "pw.x"

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


def draw_box(text):
    len_text = len(text)
    padding = 2
    return_text = "╭" + "─"*(padding*2+len_text) + "╮\n"
    return_text += "│"+ " "*padding + str(text) + " "*padding + "│\n"
    return_text += "╰" + "─"*(padding*2+len_text) + "╯\n"
    return return_text


def process_path(i, items: dict):
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

def split_arrow(i, items: list):
    return items[i].split("->")

def add_suffix(text: str, suffix: str):
    return f"{text}-{suffix}"


