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

    origin_corner_to_origin_offset_scale = {
        "xminyminzmin": Vector((1.0, 1.0, 1.0)),
        "xmaxyminzmin": Vector((-1.0, 1.0, 1.0)),
        "xminymaxzmin": Vector((1.0, -1.0, 1.0)),
        "xmaxymaxzmin": Vector((-1.0, -1.0, 1.0)),
        "xminyminzmax": Vector((1.0, 1.0, -1.0)),
        "xmaxyminzmax": Vector((-1.0, 1.0, -1.0)),
        "xminymaxzmax": Vector((1.0, -1.0, -1.0)),
        "xmaxymaxzmax": Vector((-1.0, -1.0, -1.0))
    }
    @staticmethod
    def create_piece(piece_size: WorkpieceSize,
                     origin_offset_scale: Vector) -> bmesh.types.BMesh:
        mesh = bmesh.new()

        len_offset = piece_size.length / 2.0
        width_offset = piece_size.width / 2.0
        thickness_offset = piece_size.thickness / 2.0

        origin_offset = Vector((origin_offset_scale[0] * len_offset,
                                origin_offset_scale[1] * width_offset,
                                origin_offset_scale[2] * thickness_offset))

        coords = (Vector((-len_offset, -width_offset, -thickness_offset)),
                  Vector((len_offset, -width_offset, -thickness_offset)),
                  Vector((-len_offset, width_offset, -thickness_offset)),
                  Vector((len_offset, width_offset, -thickness_offset)),
                  Vector((-len_offset, -width_offset, thickness_offset)),
                  Vector((len_offset, -width_offset, thickness_offset)),
                  Vector((-len_offset, width_offset, thickness_offset)),
                  Vector((len_offset, width_offset, thickness_offset)))

        verts = []
        for co in coords:
            vert_co = co + origin_offset
            verts.append(mesh.verts.new(vert_co.to_tuple()))

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

    # Adapted from blender code "rotation_between_quats_to_quat"
    @staticmethod
    def quaternion_rotation(quat0, quat1):
        conj = quat0.conjugated()
        saved_conj = conj.copy()
        val = 1.0 / conj.dot(conj)
        saved_conj *= val
        return saved_conj.cross(quat1)

    @staticmethod
    def visible_surface_rotation(visible_surface):
        # bring visible surface in x/z axis (front view)
        rotations = []
        if visible_surface == "face grain":
            rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
        elif visible_surface == "end grain":
            rotations.append(Quaternion((0.0, 0.0, 1.0), radians(90.0)))
        return rotations

    @staticmethod
    def orientation_rotation(context, orientation, view):
        rotations = []
        if orientation == "vertical":
            if view == "top":
                rotations.append(Quaternion((0.0, 0.0, 1.0), radians(90.0)))
            elif view == "right":
                rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
            elif view == "front":
                rotations.append(Quaternion((0.0, 1.0, 0.0), radians(90.0)))
            elif view == "align":
                space_data = context.space_data
                if space_data and space_data.type != 'VIEW_3D':
                    space_data = None
                if space_data:
                    to_user_view = space_data.region_3d.view_rotation
                    z_axis = Vector((0.0, 0.0, 1.0))
                    z_axis.rotate(to_user_view)
                    rotation_in_user_view = Quaternion(z_axis, radians(90.0))
                    rotations.append(rotation_in_user_view)

        return rotations

    @staticmethod
    def view_rotation(context, view):
        rotations = []
        if view == "top":
            rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
        elif view == "right":
            rotations.append(Quaternion((0.0, 0.0, 1.0), radians(90.0)))
        elif view == "align":
            space_data = context.space_data
            if space_data and space_data.type != 'VIEW_3D':
                space_data = None
            if space_data:
                # put in top view before user view
                rotations.append(Quaternion((1.0, 0.0, 0.0), radians(90.0)))
                rotations.append(space_data.region_3d.view_rotation.inverted())
        return rotations

    @staticmethod
    def origin_offset_scale(position_properties):
        if position_properties.origin_type == "center":
            origin_offset_scale = Vector((0.0, 0.0, 0.0))
        elif position_properties.origin_type == "corner":
            origin_offset_scale = \
                WorkpieceOperator.origin_corner_to_origin_offset_scale[
                    position_properties.origin_corner]
        return origin_offset_scale

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
            position_properties = piece_properties.position_properties
            origin_offset_scale = WorkpieceOperator.origin_offset_scale(
                position_properties)
            piece_mesh = WorkpieceOperator.create_piece(
                piece_properties.size_properties, origin_offset_scale)

            rotations = WorkpieceOperator.visible_surface_rotation(
                position_properties.visible_surface)
            rotations.extend(WorkpieceOperator.view_rotation(
                context,
                position_properties.view))
            rotations.extend(WorkpieceOperator.orientation_rotation(
                context,
                position_properties.orientation,
                position_properties.view))

            object.rotation_mode = 'QUATERNION'

            object_rotations = object.rotation_quaternion.copy()
            for rotation in rotations:
                object_rotations = WorkpieceOperator.quaternion_rotation(
                    rotation, object_rotations)
            object.rotation_quaternion = object_rotations

            if position_properties.origin_location == "3D cursor":
                object.location = scene.cursor_location
            elif position_properties.origin_location == "position":
                object.location = position_properties.location_coordinates
            elif position_properties.origin_location == "selected":
                if len(selected_objects) == 1:
                    selected = selected_objects[0]
                    object.location = selected.location + \
                                      Vector(position_properties.distance)
                else:
                    self.report({'WARNING'},
                                "Woodworking: One object should be selected")

            piece_mesh.to_mesh(mesh)
            piece_mesh.free()

            mesh.update()
            scene.objects.active = object
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "Woodworking: Option only valid in Object mode")
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
        position_box.label(text="Origin type")
        position_box.prop(position_properties, "origin_type", text="")

        if position_properties.origin_type == "corner":
            position_box.label(text="Selected corner (local)")
            position_box.prop(position_properties, "origin_corner", text="")
        elif position_properties.origin_type == "edge-centered":
            position_box.label(text="Selected edge")
            position_box.prop(position_properties, "origin_edge", text="")
        elif position_properties.origin_type == "face-centered":
            position_box.label(text="Selected face")
            position_box.prop(position_properties, "origin_face", text="")

        position_box.label(text="Origin location")
        position_box.prop(position_properties, "origin_location", text="")

        if position_properties.origin_location == "position":
            position_box.label(text="Coordinates")
            position_box.prop(position_properties, "location_coordinates",
                              text="")
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
        WorkpieceOperator.__draw_location_properties(position_box,
                                                     position_properties)

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
