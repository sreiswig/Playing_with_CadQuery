import cadquery as cq


def create_box(length: float = 10.0, width: float = 10.0, height: float = 10.0):
    """Parametric rectangular prism (CadQuery box). Units: millimetres."""
    return cq.Workplane("XY").box(length, width, height)


if __name__ == "__main__":
    model = create_box()
    cq.exporters.export(model, "box.step")
    print("Box model exported to box.step")

if "show_object" in globals():
    show_object(create_box())
