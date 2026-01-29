# z_show_square_loop_colors_braille.py  # braille
# Not augmenting sys.path - using std pypi install scheme

# Display a square with colored sides
#isolate except for this directory
import sys
import os

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
path_list = "\n    ".join(sys.path)
print(f"Final sys.path:\n    {path_list}")
##from turtle import *		     # Get standard stuff
from graphics_braille.wx_turtle_braille import *		     # Get braille
colors = ["red","orange","yellow","green"]

for colr in colors:
    width(40)
    color(colr)
    forward(200)
    right(90)
done()		    # Complete drawings
