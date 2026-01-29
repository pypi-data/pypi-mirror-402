# wx_square_loop_colors_snap_tracking.py  24Jan2025  crs, track
# Display a square with colored sides

import graphics_braille.wx_turtle_braille as tu    # Get our graphics

from graphics_braille.select_trace import SlTrace
import graphics_braille.canvas_copy as canvas_copy
SlTrace.setFlags("snapshot")
SlTrace.setFlags("user,host,rpc")
colors = ["red","orange","yellow","green"]
canvas =   tu.getcanvas()
cv_str = canvas_copy.canvas_show_items(canvas,
                    show_coords=False,
                    show_options=True,
                    use_value_cache=True)

SlTrace.lg(f"Beginning: cv_str:{cv_str}", "canvas_copy")
nside = 0
tu.snapshot(f"Begining - before square")
for color in colors:
    nside += 1
    tu.width(40)
    tu.color(color)
    tu.forward(200)
    tu.right(90)
    cv_str = canvas_copy.canvas_show_items(canvas,
                    show_coords=False,
                    show_options=True,
                    use_value_cache=True)
    SlTrace.lg(f"side{nside}: {color}: cv_str:{cv_str}", "canvas_copy")
    tu.snapshot(f"side{nside}: {color}")
tu.done()		    # Complete drawings
