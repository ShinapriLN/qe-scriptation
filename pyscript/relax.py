
from pathlib import Path

######### Don't forget to change the path!!!1
project_path = Path("mg2feh6")


def get_position(file):
    with open(file, "r") as f:
        content = f.read()

    start_idx = content.rfind("ATOMIC_POSITIONS (crystal)")
    end_idx = content.rfind("End final coordinates")

    return content[start_idx:end_idx].strip().splitlines()[1:]


def get_relax_position():
    position_list = get_position(project_path / "relax/relax.out")
    
    return "\n   ".join(position_list)
