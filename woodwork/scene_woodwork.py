import bpy
from bpy.props import *

from . piece_properties import WorkpiecePropertyGroup
from . tenon_properties import TenonPropertyGroup
from . mortise_properties import MortisePropertyGroup


class SceneWoodworkProperties(bpy.types.PropertyGroup):
    piece_properties = bpy.props.PointerProperty(type=WorkpiecePropertyGroup)
    tenon_properties = bpy.props.PointerProperty(type=TenonPropertyGroup)
    mortise_properties = bpy.props.PointerProperty(type=MortisePropertyGroup)


def register():
    bpy.utils.register_class(SceneWoodworkProperties)
    bpy.types.Scene.woodwork = bpy.props.PointerProperty(
        type=SceneWoodworkProperties)


def unregister():
    del bpy.types.Scene.woodwork
    bpy.utils.unregister_class(SceneWoodworkProperties)
