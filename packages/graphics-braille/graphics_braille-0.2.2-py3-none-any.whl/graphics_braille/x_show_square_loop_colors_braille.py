# x_show_square_loop_colors_braille.py  # braille
# Display a square with colored sides
#isolate except for this directory
import sys
import os

path_list = "\n    ".join(sys.path)
print(f"""Initial sys.path:\n    {path_list}""")
src_file = os.path.abspath(__file__)
print(f"add_src_dir file: {src_file}")
src_path = os.path.dirname(src_file)
if src_path not in sys.path:
    print(f"Inserting source directory {src_path}")
    sys.path.insert(0, src_path)
    path_list = "\n    ".join(sys.path)
    print(f"sys.path:\n    {path_list}")

file_dir = os.path.dirname(__file__)
def remove_path_ending(ending=None):
    """ Remove all sys.path entries ending in 
    :ending: ending of path to be removed
    """
    found = True
    while found:
        found = False       # Set if any found
        sys_path = sys.path
        for ent in sys.path:
            if ent.endswith(ending):
                sys_path.remove(ent)
                print(f"Removing: {ent}")
                found = True
        if found:
            sys.path = sys_path
                
remove_path_ending(r"\resource_lib\src")
if len(sys.argv) > 1:
    hack_dir = r"c:\Users\raysm\vscode\testing\venv\Lib\site-packages\graphics_braille"
    print(f"adding: {hack_dir}")
    sys.path.append(hack_dir)
path_list = "\n    ".join(sys.path)
print("clearFlags -  to minimize trace")
#import graphics_braille
from graphics_braille.select_trace import SlTrace

print(f"Final sys.path:\n    {path_list}")
##from turtle import *		     # Get standard stuff
from wx_turtle_braille import *		     # Get braille

SlTrace.clearFlags()
colors = ["red","orange","yellow","green"]

for colr in colors:
    width(40)
    color(colr)
    forward(200)
    right(90)
done()		    # Complete drawings
