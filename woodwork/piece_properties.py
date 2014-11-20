import bpy
from bpy.props import *


class WorkpieceSize(bpy.types.PropertyGroup):
    thickness = bpy.props.FloatProperty(
        name="Thickness",
        description="Thickness value",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    length = bpy.props.FloatProperty(
        name="Length",
        description="Length value",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    width = bpy.props.FloatProperty(
        name="Width",
        description="Width value",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)


class WorkpiecePosition(bpy.types.PropertyGroup):
    visible_surface = bpy.props.EnumProperty(
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

    orientation = bpy.props.EnumProperty(
        items=[('horizontal',
                "Horizontal",
                "Put visible surface horizontally"),
               ('vertical',
                "Vertical",
                "Put visible surface vertically")
               ],
        name="Orientation",
        default='horizontal')

    view = bpy.props.EnumProperty(
        items=[('top',
                "Top",
                "Put visible surface in top view"),
               ('front',
                "Front",
                "Put visible surface in front view"),
               ('right',
                "Right",
                "Put visible surface in right view"),
               ('align',
                "Align to view",
                "Align visible surface to active view")
               ],
        name="View",
        default='front')


class WorkpiecePropertyGroup(bpy.types.PropertyGroup):
    size_properties = bpy.props.PointerProperty(
        type=WorkpieceSize)
    position_properties = bpy.props.PointerProperty(
        type=WorkpiecePosition)


def register():
    bpy.utils.register_class(WorkpieceSize)
    bpy.utils.register_class(WorkpiecePosition)
    bpy.utils.register_class(WorkpiecePropertyGroup)


def unregister():
    bpy.utils.unregister_class(WorkpiecePropertyGroup)
    bpy.utils.unregister_class(WorkpiecePosition)
    bpy.utils.unregister_class(WorkpieceSize)
