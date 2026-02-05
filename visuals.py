from cadquery import *
from cadquery.vis import show

w = Workplane().sphere(1).split(keepBottom=True) - Workplane().sphere(0.5)
r = w.faces('>Z').fillet(0.1)

show(r, alpha=0.5)
