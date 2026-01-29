# show_square_loop_colors_braille_star.py  # braille
# Display a square with colored sides

##from turtle import *		     # Get standard stuff
#import graphics_braille
from graphics_braille.wx_turtle_braille import *		     # Get braille

colors = ["red","orange","yellow","green"]

for colr in colors:
    width(40)
    color(colr)
    forward(200)
    right(90)
done()		    # Complete drawings
