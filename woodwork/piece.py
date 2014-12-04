import bpy
import bmesh
from math import (
    radians
)
from mathutils import (
    Matrix,
    Vector,
    Quaternion
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
        faces = []
        for side in sides:
            side_verts = [verts[i] for i in side]
            faces.append(mesh.faces.new(side_verts))

        bmesh.ops.recalc_face_normals(mesh, faces=faces)

        return mesh

    @staticmethod
    def visible_surface_rotation(visible_surface):
        rotations = []
        if visible_surface == "edge grain":
            rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
        elif visible_surface == "end grain":
            rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
            rotations.append(Quaternion((0.0, 1.0, 0.0), radians(90.0)))
        return rotations

    @staticmethod
    def orientation_rotation(orientation):
        rotations = []
        if orientation == "vertical":
            rotations.append(Quaternion((0.0, 0.0, 1.0), radians(90.0)))
        return rotations

    @staticmethod
    def view_rotation(context, view):
        rotations = []
        if view == "front":
            rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
        elif view == "right":
            rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
            rotations.append(Quaternion((0.0, 0.0, 1.0), radians(90.0)))
        elif view == "align":
            space_data = context.space_data
            if space_data and space_data.type != 'VIEW_3D':
                space_data = None
            if space_data:
                rotations.append(space_data.region_3d.view_rotation)
        return rotations

    def execute(self, context):
        if bpy.context.mode == "OBJECT":

            scene = context.scene

            # save selected object
            selected_objects = context.selected_objects
            if len(selected_objects) > 0:
                for ob in scene.objects:
                    ob.select = False
            mesh = bpy.data.meshes.new("Workpiece")
            object = bpy.data.objects.new("Workpiece", mesh)
            base = scene.objects.link(object)
            base.select = True

            piece_properties = self.piece_properties
            piece_mesh = WorkpieceOperator.create_piece(piece_properties.size_properties)

            position_properties = piece_properties.position_properties

            visible = WorkpieceOperator.visible_surface_rotation(position_properties.visible_surface)
            orientation = WorkpieceOperator.orientation_rotation(position_properties.orientation)
            view = WorkpieceOperator.view_rotation(context, position_properties.view)

            for rotation in visible:
                bmesh.ops.transform(piece_mesh,
                                    matrix=rotation.to_matrix(),
                                    verts=piece_mesh.verts)
            for rotation in orientation:
                bmesh.ops.transform(piece_mesh,
                                    matrix=rotation.to_matrix(),
                                    verts=piece_mesh.verts)
            for rotation in view:
                bmesh.ops.transform(piece_mesh,
                                    matrix=rotation.to_matrix(),
                                    verts=piece_mesh.verts)

            if position_properties.origin_location == "3D cursor":
                object.location = scene.cursor_location
            elif position_properties.origin_location == "position":
                object.location = position_properties.location_coordinates
            elif position_properties.origin_location == "selected":
                if len(selected_objects) == 1:
                    selected = selected_objects[0]
                    object.location = selected.location + Vector(position_properties.distance)
                else:
                    self.report({'WARNING'}, "Woodworking: One object should be selected")

            piece_mesh.to_mesh(mesh)
            piece_mesh.free()

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
    def __draw_location_properties(position_box, position_properties):
        position_box.label(text="Origin location")
        position_box.prop(position_properties, "origin_location", text="")

        if position_properties.origin_location == "position":
            position_box.label(text="Coordinates", icon='MANIPUL')
            position_box.prop(position_properties, "location_coordinates", text="")
        elif position_properties.origin_location == "selected":
            position_box.label(text="Distance", icon='ARROW_LEFTRIGHT')
            position_box.prop(position_properties, "distance", text="")

    @staticmethod
    def __draw_position_properties(layout, position_properties):
        position_box = layout.box()

        position_box.label(text="Visible face", icon="SNAP_FACE")
        position_box.prop(position_properties, "visible_surface", text="")
        position_box.label(text="Orientation", icon="FILE_REFRESH")
        position_box.prop(position_properties, "orientation", text="")
        position_box.label(text="View", icon="RESTRICT_VIEW_OFF")
        position_box.prop(position_properties, "view", text="")
        WorkpieceOperator.__draw_location_properties(position_box, position_properties)

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
