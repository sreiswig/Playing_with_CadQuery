import cadquery as cq

def tidy_repr(obj):
    """Shortens a default repr string"""
    return repr(obj).split(".")[-1].rstrip(">")

def _ctx_str(self):
    return (
        tidy_repr(self)
        + ":\n"
        + f"    pendingWires: {self.pendingWires}\n"
        + f"    pendingEdges: {self.pendingEdges}\n"
        + f"    tags: {self.tags}"
    )

cq.cq.CQContext.__str__ = _ctx_str

def _plane_str(self):
    return (
        tidy_repr(self)
        + ":\n"
        + f"    origin: {self.origin.toTuple()}\n"
        + f"    z direction: {self.zDir.toTuple()}"
    )

cq.occ_impl.geom.Plane.__str__ = _plane_str


def _wp_str(self):
    out = tidy_repr(self) + ":\n"
    out += f"   parent: {tidy_repr(self.parent)}\n" if self.parent else " no parent\n"
    out += f"   plane: {self.plane}\n"
    out += f"   objects: {self.objects}\n"
    out += f"   modelling context: {self.ctx}"
    return out


cq.Workplane.__str__ = _wp_str
