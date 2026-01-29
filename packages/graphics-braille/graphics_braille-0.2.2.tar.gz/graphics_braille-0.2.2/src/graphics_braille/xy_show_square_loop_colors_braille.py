# xy_show_square_loop_colors_braille.py  # force adding hack_dir
# Display a square with colored sides
#isolate except for this directory
import sys
import os
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
if True or len(sys.argv) > 1:   # Force
    hack_dir = r"c:\Users\raysm\vscode\testing\venv\Lib\site-packages\graphics_braille"
    print(f"adding: {hack_dir}")
    sys.path.append(hack_dir)
print(f"sys.path:\n    {"\n    ".join(sys.path)}")
##from turtle import *		     # Get standard stuff
from wx_turtle_braille import *		     # Get braille

colors = ["red","orange","yellow","green"]

for colr in colors:
    width(40)
    color(colr)
    forward(200)
    right(90)
done()		    # Complete drawings
