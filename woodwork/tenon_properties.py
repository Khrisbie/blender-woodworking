import bpy
from bpy.props import *

class TenonThicknessPropertyGroup(bpy.types.PropertyGroup):
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
                    name = "Thickness",
                    description = "Tenon thickness (relative to width side)",
                    min = 0.0,
                    default = -1.0,
                    subtype = 'DISTANCE',
                    unit = 'LENGTH',
                    precision = 3,
                    step = 0.1)

    percentage = bpy.props.FloatProperty(
                    name = "Thickness",
                    description = "Tenon thickness (relative to width side)",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    centered = bpy.props.BoolProperty(
                    name = "Centered",
                    description = "Specify if tenon is centered on width side",
                    default = True)

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
                    name = "Shoulder",
                    description = "Tenon shoulder on width side",
                    min = 0.0,
                    default = -1.0,
                    subtype = 'DISTANCE',
                    unit = 'LENGTH',
                    precision = 3,
                    step = 0.1)

    shoulder_percentage = bpy.props.FloatProperty(
                    name = "Shoulder",
                    description = "Tenon shoulder (relative to width side)",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    reverse_shoulder = bpy.props.BoolProperty(
                    name = "Reverse shoulder",
                    description = "Specify shoulder for the other side",
                    default = False)

class TenonHeightPropertyGroup(bpy.types.PropertyGroup):
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
                        name = "Height",
                        description = "Tenon height relative to length side",
                        min = 0.0,
                        default = -1.0,
                        subtype = 'DISTANCE',
                        unit ='LENGTH',
                        precision = 3,
                        step = 0.1)

    percentage = bpy.props.FloatProperty(
                    name = "Height",
                    description = "Tenon height relative to length side",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    centered = bpy.props.BoolProperty(
                    name = "Centered",
                    description = "Specify if tenon is centered on length side",
                    default = True)

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
                    name = "Shoulder",
                    description = "Tenon shoulder on length side",
                    min = 0.0,
                    default = -1.0,
                    subtype = 'DISTANCE',
                    unit = 'LENGTH',
                    precision = 3,
                    step = 0.1)

    shoulder_percentage = bpy.props.FloatProperty(
                    name = "Shoulder",
                    description = "Tenon shoulder (relative to length side)",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    reverse_shoulder = bpy.props.BoolProperty(
                    name = "Reverse shoulder",
                    description = "Specify shoulder for the other side",
                    default = False)

class TenonPropertyGroup(bpy.types.PropertyGroup):

    thickness_properties = bpy.props.PointerProperty(type = TenonThicknessPropertyGroup)
    height_properties = bpy.props.PointerProperty(type = TenonHeightPropertyGroup)

    depth_value = bpy.props.FloatProperty(
                        name = "Depth",
                        description = "Tenon depth",
                        min = 0.0,
                        default = -1.0,
                        subtype = 'DISTANCE',
                        unit = 'LENGTH',
                        precision = 3,
                        step = 0.1)

def register():
    bpy.utils.register_class(TenonThicknessPropertyGroup)
    bpy.utils.register_class(TenonHeightPropertyGroup)
    bpy.utils.register_class(TenonPropertyGroup)
    bpy.types.Scene.tenonProperties = bpy.props.PointerProperty(type = TenonPropertyGroup)

def unregister():
    bpy.utils.unregister_class(TenonThicknessPropertyGroup)
    bpy.utils.unregister_class(TenonHeightPropertyGroup)
    bpy.utils.unregister_class(TenonPropertyGroup)


#----------------------------------------------
# Code to run the script alone
#----------------------------------------------
if __name__ == "__main__":
    register()
    print("Executed")
