# wx_spokes.py  16Jul2024  crs use wx_turtle_braille directly
#               20Jan2024, crs from spokes.py
# Display a star with spokes

import graphics_braille.wx_turtle_braille as tu        # Set for wxPython
#import turtle as tu    # Bring in turtle graphic functions
tu.speed("fastest")
colors = ["red","orange","yellow",
          "green","blue","indigo","violet"]
for colr in colors:      # do all colors in list
    tu.color(colr)
    tu.forward(300)
    tu.dot(100)
    tu.backward(300)
    tu.right(360/len(colors))
tu.done()
