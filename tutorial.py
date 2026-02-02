import cadquery as cq

dh = 2
r = 1

# 1. Define the profiles at different Z heights
# We use a list of wires to loft through
path = cq.Workplane("XY")
edge1 = cq.Workplane("XY").circle(r)
edge2 = cq.Workplane("XY").center(0, 0).workplane(offset=dh).circle(1.5 * r)
edge3 = cq.Workplane("XY").center(0, 0).workplane(offset=1.5 * dh).circle(r)

# 2. Loft the profiles to create the side shell
# We combine the wires into a single object and loft them
side = cq.Workplane("XY").add(edge1).add(edge2).add(edge3).loft(ruled=False)

# 3. Create a solid by closing the loft
# In the Fluent API, .loft(combine=True) often handles the faces, 
# but for manual capping like your tutorial:
result = side.faces(">Z").shell(0) # Simple way to make it a solid shell

# 4. Moving the object (as per your tutorial logic)
result = result.translate((-3 * r, 0, 0))

# Exporting for your verification
cq.exporters.export(result, 'result.step')

# If using CQ-Editor, this displays it
if 'show_object' in globals():
    show_object(result)
