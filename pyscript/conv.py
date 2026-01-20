import os
from pathlib import Path

######### Don't forget to change the path!!!1
project_path = Path("mg2feh6")

KP = [4, 5, 6, 7, 8]
TEST_ECUT = [30.0, 40.0, 50.0, 60.0, 70.0, 80.0]


def get_energy(path):
    with open(path, "r") as f:
        content = f.read()
    start_idx = content.rfind("!")
    end_idx = content.find("Ry", start_idx)
    e = float(content[start_idx:end_idx].split("=")[-1].strip())
    return e

def get_best_E_idx(E, threshold):
    
    assert len(E) > 0, "no members in E list."

    if len(E) == 1:
        return 0
    
    e_0 = E[0]
    for i, energy in enumerate(E):
        if i == 0:
            continue

        if e_0 - energy <= threshold:    
            return i
        
        e_0 = energy

    return len(E) - 1
        

def get_best_ecutwfc():

    threshold = 1e-6

    filename = [f"conv-{i}/conv-{i}.out" for i in range(6)]
    E = [get_energy(project_path/f) for f in filename]
    idx = get_best_E_idx(E, threshold)
    return TEST_ECUT[idx]


def get_best_ecutrho():

    threshold = 1e-6

    filename = [f"conv-{i}/conv-{i}.out" for i in range(6)]
    E = [get_energy(project_path/f) for f in filename]
    idx = get_best_E_idx(E, threshold)
    return TEST_ECUT[idx] * 8


def get_best_kp():
    threshold = 1e-6

    filename = [f"conv-{i}/conv-{i}.out" for i in range(6, 11)]
    E = [get_energy(project_path/f) for f in filename]
    idx = get_best_E_idx(E, threshold)

    kp = KP[idx]
    return f"{kp} {kp} {kp} 1 1 1"
