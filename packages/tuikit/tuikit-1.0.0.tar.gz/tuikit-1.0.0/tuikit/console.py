from .textools import style_text, Align
from . import logictools  
import os

def spacer(times):
    for _ in range(times): print()

def underline(line: str="—", hue: str="", alone=False, return_str: bool = False):
    term_width = logictools.get_term_size(True)
    output = ""
    line = style_text(line*term_width, hue)
    if alone:
        if not return_str: print()
        output += "\n"
    if not return_str: print(line)
    else: output += line
    if alone:
        if not return_str: print()
        output += "\n"
    return output

def clear(header=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    if header: print(header)