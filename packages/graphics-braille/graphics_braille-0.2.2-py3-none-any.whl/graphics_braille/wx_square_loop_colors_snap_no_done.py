# wx_square_loop_colors.py  26Jul2024  crs, use wx_turtle_braille.py directly
# Display a square with colored sides

import graphics_braille.wx_turtle_braille as tu    # Get our graphics
##from turtle import *		     # Get standard stuff
from graphics_braille.select_trace import SlTrace
import graphics_braille.canvas_copy as canvas_copy

SlTrace.setFlags("user,host")
colors = ["red","orange","yellow","green"]

nside = 0
for color in colors:
    nside += 1
    tu.width(40)
    tu.color(color)
    tu.forward(200)
    tu.right(90)
    tu.snapshot(f"side{nside}: {color}")
#tu.done()		    # Complete drawings
