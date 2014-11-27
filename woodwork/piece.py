import bpy
import bmesh
from mathutils import (
    Matrix,
    Vector
)

from . piece_properties import (
    WorkpiecePropertyGroup,
    WorkpieceSize
)


class WorkpieceOperator(bpy.types.Operator):
    bl_description = "Creates a new workpiece"
    bl_idname = "mesh.woodwork_workpiece"
    bl_label = "Workpiece"
    bl_category = 'Woodwork'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    #
    # Class variables
    #
    expand_size_properties = bpy.props.BoolProperty(name="Expand",
                                                    default=True)
    expand_position_properties = bpy.props.BoolProperty(name="Expand",
                                                        default=True)

    piece_properties = bpy.props.PointerProperty(type=WorkpiecePropertyGroup)

    @staticmethod
    def create_piece(piece_size: WorkpieceSize) -> bmesh.types.BMesh:
        mesh = bmesh.new()

        len_offset = piece_size.length / 2.0
        width_offset = piece_size.width / 2.0
        thickness_offset = piece_size.thickness / 2.0

        coords = ((-len_offset, -width_offset, -thickness_offset),
                  (len_offset, -width_offset, -thickness_offset),
                  (-len_offset, width_offset, -thickness_offset),
                  (len_offset, width_offset, -thickness_offset),
                  (-len_offset, -width_offset, thickness_offset),
                  (len_offset, -width_offset, thickness_offset),
                  (-len_offset, width_offset, thickness_offset),
                  (len_offset, width_offset, thickness_offset))

        verts = []
        for co in coords:
            verts.append(mesh.verts.new(co))

        sides = ((0, 2, 3, 1),
                 (4, 5, 7, 6),
                 (0, 4, 5, 1),
                 (1, 3, 7, 5),
                 (3, 7, 6, 2),
                 (2, 0, 4, 6))
        for side in sides:
            side_verts = [verts[i] for i in side]
            mesh.faces.new(side_verts)

        return mesh


    def execute(self, context):
        if bpy.context.mode == "OBJECT":

            scene = context.scene
            for ob in scene.objects:
                ob.select = False
            mesh = bpy.data.meshes.new("Workpiece")
            object = bpy.data.objects.new("Workpiece", mesh)
            object.location = scene.cursor_location
            base = scene.objects.link(object)
            base.select = True

            piece_properties = self.piece_properties
            piece_mesh = WorkpieceOperator.create_piece(piece_properties.size_properties)
            piece_mesh.to_mesh(mesh)
            mesh.update()
            scene.objects.active = object
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Woodworking: Option only valid in Object mode")
            return {'CANCELLED'}

    @staticmethod
    def __draw_size_properties(layout, size_properties):
        size_box = layout.box()

        size_box.label(text="Thickness")
        size_box.prop(size_properties, "thickness", text="")
        size_box.label(text="Length")
        size_box.prop(size_properties, "length", text="")
        size_box.label(text="Width")
        size_box.prop(size_properties, "width", text="")

    @staticmethod
    def __draw_position_properties(layout, position_properties):
        position_box = layout.box()

        position_box.label(text="Visible face")
        position_box.prop(position_properties, "visible_surface", text="")
        position_box.label(text="Orientation")
        position_box.prop(position_properties, "orientation", text="")
        position_box.label(text="View")
        position_box.prop(position_properties, "view", text="")

    def draw(self, context):
        layout = self.layout

        piece_properties = self.piece_properties
        size_properties = piece_properties.size_properties
        position_properties = piece_properties.position_properties

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if not self.expand_size_properties:
            row.prop(self, "expand_size_properties", icon="TRIA_RIGHT",
                     icon_only=True, text="Size",
                     emboss=False)
        else:
            row.prop(self, "expand_size_properties", icon="TRIA_DOWN",
                     icon_only=True, text="Size",
                     emboss=False)
            WorkpieceOperator.__draw_size_properties(layout,
                                                     size_properties)

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if not self.expand_position_properties:
            row.prop(self, "expand_position_properties", icon="TRIA_RIGHT",
                     icon_only=True, text="Position",
                     emboss=False)
        else:
            row.prop(self, "expand_position_properties", icon="TRIA_DOWN",
                     icon_only=True, text="Position",
                     emboss=False)
            WorkpieceOperator.__draw_position_properties(layout,
                                                         position_properties)


def register():
    bpy.utils.register_class(WorkpieceOperator)


def unregister():
    bpy.utils.unregister_class(WorkpieceOperator)
