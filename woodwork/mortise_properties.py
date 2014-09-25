import bpy
from bpy.props import *


class MortiseThicknessPropertyGroup(bpy.types.PropertyGroup):
    type = bpy.props.EnumProperty(
        items=[('max',
                "Max. thickness",
                "Set thickness to the maximum width"),
               ('value',
                "Value",
                "Give value to thickness"),
               ('percentage',
                "Percentage",
                "Set thickness by percentage")],
        name="Thickness type",
        default='value')

    value = bpy.props.FloatProperty(
        name="Thickness",
        description="Mortise thickness (relative to width side)",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    percentage = bpy.props.FloatProperty(
        name="Thickness",
        description="Mortise thickness (relative to width side)",
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE')

    centered = bpy.props.BoolProperty(
        name="Centered",
        description="Specify if mortise is centered on width side",
        default=True)

    shoulder_type = bpy.props.EnumProperty(
        items=[('value',
                "Value",
                "Give value to shoulder thickness"),
               ('percentage',
                "Percentage",
                "Set thickness shoulder by percentage")],
        name="Thickness shoulder type",
        default='value')

    shoulder_value = bpy.props.FloatProperty(
        name="Shoulder",
        description="Mortise shoulder on width side",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    shoulder_percentage = bpy.props.FloatProperty(
        name="Shoulder",
        description="Mortise shoulder (relative to width side)",
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE')

    reverse_shoulder = bpy.props.BoolProperty(
        name="Reverse shoulder",
        description="Specify shoulder for the other side",
        default=False)


class MortiseHeightPropertyGroup(bpy.types.PropertyGroup):
    type = bpy.props.EnumProperty(
        items=[('max',
                "Max. height",
                "Set height to the maximum length"),
               ('value',
                "Value",
                "Give value to height"),
               ('percentage',
                "Percentage",
                "Set height by percentage")],
        name="Height type",
        default='value')

    value = bpy.props.FloatProperty(
        name="Height",
        description="Mortise height relative to length side",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    percentage = bpy.props.FloatProperty(
        name="Height",
        description="Mortise height relative to length side",
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE')

    centered = bpy.props.BoolProperty(
        name="Centered",
        description="Specify if mortise is centered on length side",
        default=True)

    shoulder_type = bpy.props.EnumProperty(
        items=[('value',
                "Value",
                "Give value to shoulder height"),
               ('percentage',
                "Percentage",
                "Set shoulder height by percentage")],
        name="Height shoulder type",
        default='value')

    shoulder_value = bpy.props.FloatProperty(
        name="Shoulder",
        description="Mortise shoulder on length side",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    shoulder_percentage = bpy.props.FloatProperty(
        name="Shoulder",
        description="Mortise shoulder (relative to length side)",
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE')

    reverse_shoulder = bpy.props.BoolProperty(
        name="Reverse shoulder",
        description="Specify shoulder for the other side",
        default=False)

    haunched = bpy.props.BoolProperty(
        name="Haunched",
        description="Add a little stub mortise at the top of the joint",
        default=False)

    haunch_type = bpy.props.EnumProperty(
        items=[('value',
                "Value",
                "Give value to haunch depth"),
               ('percentage',
                "Percentage",
                "Set haunch depth by percentage")],
        name="Haunch value type",
        default='value')

    haunch_depth_value = bpy.props.FloatProperty(
        name="Haunch depth",
        description="Haunch depth",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)

    haunch_depth_percentage = bpy.props.FloatProperty(
        name="Haunch depth",
        description="Haunch depth (relative to mortise depth)",
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE')

    haunch_angle = bpy.props.EnumProperty(
        items=[('straight',
                "Straight",
                "Use a straight haunch"),
               ('sloped',
                "Sloped",
                "Use a sloping haunch")],
        name="Haunch angle",
        default='straight')


class MortisePropertyGroup(bpy.types.PropertyGroup):
    thickness_properties = bpy.props.PointerProperty(
        type=MortiseThicknessPropertyGroup)
    height_properties = bpy.props.PointerProperty(type=MortiseHeightPropertyGroup)

    depth_value = bpy.props.FloatProperty(
        name="Depth",
        description="Mortise depth",
        min=0.0,
        default=-1.0,
        subtype='DISTANCE',
        unit='LENGTH',
        precision=3,
        step=0.1)


def register():
    bpy.utils.register_class(MortiseThicknessPropertyGroup)
    bpy.utils.register_class(MortiseHeightPropertyGroup)
    bpy.utils.register_class(MortisePropertyGroup)

    bpy.types.Scene.mortiseProperties = bpy.props.PointerProperty(
        type=MortisePropertyGroup)

def unregister():
    bpy.utils.unregister_class(MortisePropertyGroup)
    bpy.utils.unregister_class(MortiseHeightPropertyGroup)
    bpy.utils.unregister_class(MortiseThicknessPropertyGroup)

    del bpy.types.Scene.mortiseProperties

# ----------------------------------------------
# Code to run the script alone
#----------------------------------------------
if __name__ == "__main__":
    register()
