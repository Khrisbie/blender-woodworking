import bpy.utils
from bpy.props import (
    FloatProperty,
    EnumProperty,
    PointerProperty,
    FloatVectorProperty
)
from bpy.types import (
    PropertyGroup
)


class WorkpieceSize(PropertyGroup):
    thickness = FloatProperty(
        name="Thickness",
        description="Thickness value",
        min=0.0,
        default=0.02,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=4,
        step=0.01)

    length = FloatProperty(
        name="Length",
        description="Length value",
        min=0.0,
        default=0.2,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=4,
        step=0.01)

    width = FloatProperty(
        name="Width",
        description="Width value",
        min=0.0,
        default=0.05,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=4,
        step=0.01)


class WorkpiecePosition(PropertyGroup):
    visible_surface = EnumProperty(
        items=[('edge grain',
                "Edge grain",
                "Set side of the board as front face"),
               ('end grain',
                "End grain",
                "Set end of the board as front face"),
               ('face grain',
                "Face grain",
                "Set the outside of the board as front face")
               ],
        name="Visible surface",
        default='face grain')

    orientation = EnumProperty(
        items=[('horizontal',
                "Horizontal",
                "Put visible surface horizontally"),
               ('vertical',
                "Vertical",
                "Put visible surface vertically")
               ],
        name="Orientation",
        default='horizontal')

    view = EnumProperty(
        items=[('top',
                "Top",
                "Put visible surface in top view",
                "AXIS_TOP",
                0),
               ('front',
                "Front",
                "Put visible surface in front view",
                "AXIS_FRONT",
                1),
               ('right',
                "Right",
                "Put visible surface in right view",
                "AXIS_SIDE",
                2),
               ('align',
                "Align to view",
                "Align visible surface to active view",
                "VIEW3D",
                3)
               ],
        name="View",
        default='front')


    origin_location = EnumProperty(
        items=[('3D cursor',
                "3D Cursor",
                "Set location to 3D cursor"),
               ('center',
                "Center",
                "Set location to scene center"),
               ('position',
                "Position",
                "Enter location coordinates"),
               ('selected',
                "Near selected",
                "Put piece near selected object")],
        name="Origin location",
        default='3D cursor'
    )

    location_coordinates = FloatVectorProperty(
        name="Location",
        subtype="XYZ"
    )

    distance = FloatVectorProperty(
        name="Distance",
        description="Distance between the elements in BUs",
        subtype="DIRECTION",
        unit="LENGTH",
        default=(0.1, 0.0, 0.0))

class WorkpiecePropertyGroup(PropertyGroup):
    size_properties = PointerProperty(type=WorkpieceSize)
    position_properties = PointerProperty(type=WorkpiecePosition)


def register():
    bpy.utils.register_class(WorkpieceSize)
    bpy.utils.register_class(WorkpiecePosition)
    bpy.utils.register_class(WorkpiecePropertyGroup)


def unregister():
    bpy.utils.unregister_class(WorkpiecePropertyGroup)
    bpy.utils.unregister_class(WorkpiecePosition)
    bpy.utils.unregister_class(WorkpieceSize)
