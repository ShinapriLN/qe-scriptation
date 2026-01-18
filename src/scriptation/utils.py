


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