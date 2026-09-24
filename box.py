from cq_artifacts.box_dims import DEFAULT_BOX_MM, box_deny_message, make_box_size
from cq_artifacts.outcome import Err


def create_box(
    length: float = DEFAULT_BOX_MM,
    width: float = DEFAULT_BOX_MM,
    height: float = DEFAULT_BOX_MM,
):
    """Parametric rectangular prism (CadQuery box). Units: millimetres."""
    sized = make_box_size(length, width, height)
    if isinstance(sized, Err):
        raise ValueError(box_deny_message(sized.error))
    size = sized.value
    import cadquery as cq

    return cq.Workplane("XY").box(size.length_mm, size.width_mm, size.height_mm)


if __name__ == "__main__":
    import cadquery as cq

    model = create_box()
    cq.exporters.export(model, "box.step")
    print("Box model exported to box.step")

if "show_object" in globals():
    show_object(create_box())
