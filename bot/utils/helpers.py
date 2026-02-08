import json
import os

theme_colors = [
    "#c9e6f2", "#F2D388", "#C98474", "#30475E",
    "#F1935C", "#BA6B57", "#E7B2A5", "#874C62",
]

blank_px = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z/C/HgAGgwJ/lK3Q6wAAAABJRU5ErkJggg=="


def write_json(fname, data=""):
    try:
        if not isinstance(data, str):
            data = json.dumps(data, indent=4)
        with open(fname, "w") as fp:
            fp.writelines(data)
    except Exception as e:
        raise e


def chunk_message(inpt: str) -> list:
    if len(inpt) < 2000:
        return [inpt]
    text = inpt.split("\n")
    message = ""
    parts = []
    for x in text:
        if len(message) + len(x) + 1 < 2000:
            message = message + "\n" + x
        else:
            parts.append(message)
            message = x
    return parts + [message[:2000]]
