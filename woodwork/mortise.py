import bpy
import bmesh
from tenon_mortise_builder import TenonMortiseBuilder, TenonMortiseBuilderProps, FaceToBeTransformed, nearly_equal
from tenon import is_face_planar, is_face_rectangular

class MortiseOperator(bpy.types.Operator):
    bl_description = "Creates a mortise given a face"
    bl_idname = "mesh.mortise"
    bl_label = "Mortise"
    bl_options = {'REGISTER', 'UNDO'}

    #
    # Class variables
    #

    shortest_length = -1.0
    longest_length = -1.0

    expand_thickness_properties = bpy.props.BoolProperty(name="Expand",
                                                         default=True)
    expand_height_properties = bpy.props.BoolProperty(name="Expand",
                                                      default=True)

    def __check_face(self, face):
        # If we don't find a selected face, we have problem.  Exit:
        if face is None:
            self.report({'ERROR_INVALID_INPUT'},
                        "You must select a face for the mortise.")
            return False

        # Warn the user if face is not 4 vertices.
        if len(face.verts) > 4:
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is not quad.")
            return False

        if not is_face_planar(face):
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is not planar.")
            return False

        if not is_face_rectangular(face):
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is not rectangular.")
            return False
        return True

    # Custom layout
    def draw(self, context):
        layout = self.layout

        mortise_properties = context.scene.mortiseProperties
        thickness_properties = mortise_properties.thickness_properties
        height_properties = mortise_properties.height_properties

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if not self.expand_thickness_properties:
            row.prop(self, "expand_thickness_properties", icon="TRIA_RIGHT",
                     icon_only=True, text="Width side",
                     emboss=False)
        else:
            row.prop(self, "expand_thickness_properties", icon="TRIA_DOWN",
                     icon_only=True, text="Width side",
                     emboss=False)

            width_side_box = layout.box()
            width_side_box.label(text="Thickness type")
            width_side_box.prop(thickness_properties, "type", text="")
            if thickness_properties.type == "value":
                width_side_box.prop(thickness_properties, "value", text="")
            elif thickness_properties.type == "percentage":
                width_side_box.prop(thickness_properties, "percentage", text="",
                                    slider=True)
            width_side_box.label(text="Position")
            width_side_box.prop(thickness_properties, "centered")
            if not thickness_properties.centered:
                width_side_box.label(text="Thickness shoulder type")
                width_side_box.prop(thickness_properties, "shoulder_type",
                                    text="")
                if thickness_properties.shoulder_type == "value":
                    width_side_box.prop(thickness_properties, "shoulder_value",
                                        text="")
                elif thickness_properties.shoulder_type == "percentage":
                    width_side_box.prop(thickness_properties,
                                        "shoulder_percentage", text="",
                                        slider=True)
                width_side_box.prop(thickness_properties, "reverse_shoulder")

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if not self.expand_height_properties:
            row.prop(self, "expand_height_properties", icon="TRIA_RIGHT",
                     icon_only=True, text="Length side",
                     emboss=False)
        else:
            row.prop(self, "expand_height_properties", icon="TRIA_DOWN",
                     icon_only=True, text="Length side",
                     emboss=False)

            length_side_box = layout.box()
            length_side_box.label(text="Height type")
            length_side_box.prop(height_properties, "type", text="")
            if height_properties.type == "value":
                length_side_box.prop(height_properties, "value", text="")
            elif height_properties.type == "percentage":
                length_side_box.prop(height_properties, "percentage", text="",
                                     slider=True)
            length_side_box.label(text="Position")
            length_side_box.prop(height_properties, "centered")
            if not height_properties.centered:
                length_side_box.label(text="Height shoulder type")
                length_side_box.prop(height_properties, "shoulder_type",
                                     text="")
                if height_properties.shoulder_type == "value":
                    length_side_box.prop(height_properties, "shoulder_value",
                                         text="")
                elif height_properties.shoulder_type == "percentage":
                    length_side_box.prop(height_properties,
                                         "shoulder_percentage",
                                         text="", slider=True)
                length_side_box.prop(height_properties, "reverse_shoulder")
                length_side_box.prop(height_properties, "haunched")
                if height_properties.haunched:
                    length_side_box.label(text="Haunch depth type")
                    length_side_box.prop(height_properties, "haunch_type",
                                         text="")
                    if height_properties.haunch_type == "value":
                        length_side_box.prop(height_properties,
                                             "haunch_depth_value", text="")
                    elif height_properties.haunch_type == "percentage":
                        length_side_box.prop(height_properties,
                                             "haunch_depth_percentage", text="",
                                             slider=True)
                    length_side_box.label(text="Haunch angle")
                    length_side_box.prop(height_properties, "haunch_angle",
                                         text="")

        layout.label(text="Depth")
        layout.prop(mortise_properties, "depth_value", text="")

    # used to check if the operator can run
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and context.mode == 'EDIT_MESH'

    def __mortise_properties_to_builder_properties(self, mortise_properties):
        builder_properties = TenonMortiseBuilderProps()
        builder_properties.depth_value = -mortise_properties.depth_value

        builder_thickness_properties = builder_properties.thickness_properties
        mortise_thickness_properties = mortise_properties.thickness_properties

        builder_thickness_properties.type = mortise_thickness_properties.type
        builder_thickness_properties.value = mortise_thickness_properties.value
        builder_thickness_properties.percentage = mortise_thickness_properties.percentage
        builder_thickness_properties.centered = mortise_thickness_properties.centered
        builder_thickness_properties.shoulder_type = mortise_thickness_properties.shoulder_type
        builder_thickness_properties.shoulder_value = mortise_thickness_properties.shoulder_value
        builder_thickness_properties.shoulder_percentage = mortise_thickness_properties.shoulder_percentage
        builder_thickness_properties.reverse_shoulder = mortise_thickness_properties.reverse_shoulder

        builder_height_properties = builder_properties.height_properties
        mortise_height_properties = mortise_properties.height_properties

        builder_height_properties.type = mortise_height_properties.type
        builder_height_properties.value = mortise_height_properties.value
        builder_height_properties.percentage = mortise_height_properties.percentage
        builder_height_properties.centered = mortise_height_properties.centered
        builder_height_properties.shoulder_type = mortise_height_properties.shoulder_type
        builder_height_properties.shoulder_value = mortise_height_properties.shoulder_value
        builder_height_properties.shoulder_percentage = mortise_height_properties.shoulder_percentage
        builder_height_properties.reverse_shoulder =  mortise_height_properties.reverse_shoulder
        builder_height_properties.haunched =  mortise_height_properties.haunched
        builder_height_properties.haunch_type = mortise_height_properties.haunch_type
        builder_height_properties.haunch_depth_value =  -mortise_height_properties.haunch_depth_value
        builder_height_properties.haunch_depth_percentage =  mortise_height_properties.haunch_depth_percentage
        builder_height_properties.haunch_angle =  mortise_height_properties.haunch_angle

        return builder_properties

    def execute(self, context):

        mortise_properties = context.scene.mortiseProperties
        thickness_properties = mortise_properties.thickness_properties
        height_properties = mortise_properties.height_properties

        obj = context.object
        matrix_world = obj.matrix_world
        mesh = obj.data

        if mesh.is_editmode:
            # Gain direct access to the mesh
            bm = bmesh.from_edit_mesh(mesh)
        else:
            # Create a bmesh from mesh
            # (won't affect mesh, unless explicitly written back)
            bm = bmesh.new()
            bm.from_mesh(mesh)

        # Get active face
        faces = bm.faces
        face = faces.active

        # Check if face could be transformed to mortise ...
        if not self.__check_face(face):
            return {'CANCELLED'}

        # Split edges to avoid affecting linked faces when subdividing
        edges_to_split = [edge for edge in face.edges]
        ret = bmesh.ops.split_edges(bm, edges=edges_to_split)
        del ret

        # Extract face infos
        face_to_be_transformed = FaceToBeTransformed(face)
        face_to_be_transformed.extract_features(matrix_world)

        # Init default values, look if face has changed too
        if (thickness_properties.value == -1.0 or
                (not nearly_equal(face_to_be_transformed.shortest_length,
                                  self.shortest_length))):
            thickness_properties.value = \
                face_to_be_transformed.shortest_length / 3.0
            thickness_properties.percentage = 1.0 / 3.0
            thickness_properties.centered = True
        if (height_properties.value == -1.0 or
                (not nearly_equal(face_to_be_transformed.longest_length,
                                  self.longest_length))):
            height_properties.value = (face_to_be_transformed.longest_length *
                                       2.0) / 3.0
            height_properties.percentage = 2.0 / 3.0
            height_properties.centered = True
        if (mortise_properties.depth_value == -1.0 or
                (not nearly_equal(face_to_be_transformed.longest_length,
                                  self.longest_length))):
            mortise_properties.depth_value = \
                face_to_be_transformed.shortest_length
            height_properties.haunch_depth_value = \
                mortise_properties.depth_value / 3.0
            height_properties.haunch_depth_percentage = 1.0 / 3.0

        # used to reinit default values when face changes
        self.shortest_length = face_to_be_transformed.shortest_length
        self.longest_length = face_to_be_transformed.longest_length

        # If percentage specified, compute length values
        if thickness_properties.type == "percentage":
            thickness_properties.value = \
                face_to_be_transformed.shortest_length * \
                thickness_properties.percentage

        if height_properties.type == "percentage":
            height_properties.value = face_to_be_transformed.longest_length * \
                height_properties.percentage

        # Init values linked to shoulder size
        if thickness_properties.centered:
            thickness_properties.shoulder_value = ((
                face_to_be_transformed.shortest_length -
                thickness_properties.value) / 2.0)
            thickness_properties.shoulder_percentage = \
                thickness_properties.shoulder_value / \
                face_to_be_transformed.shortest_length
        if height_properties.centered:
            height_properties.shoulder_value = ((
                face_to_be_transformed.longest_length -
                height_properties.value) / 2.0)
            height_properties.shoulder_percentage = \
                height_properties.shoulder_value / \
                face_to_be_transformed.longest_length

        # If shoulder percentage specified, compute length values
        if thickness_properties.shoulder_type == "percentage":
            thickness_properties.shoulder_value = \
                face_to_be_transformed.shortest_length * \
                thickness_properties.shoulder_percentage
            if (thickness_properties.shoulder_value +
                    thickness_properties.value >
                    face_to_be_transformed.shortest_length):
                thickness_properties.value = \
                    face_to_be_transformed.shortest_length - \
                    thickness_properties.shoulder_value
                thickness_properties.percentage =\
                    thickness_properties.value / \
                    face_to_be_transformed.shortest_length

        if height_properties.shoulder_type == "percentage":
            height_properties.shoulder_value = \
                face_to_be_transformed.longest_length * \
                height_properties.shoulder_percentage
            if (height_properties.shoulder_value + height_properties.value >
                    face_to_be_transformed.longest_length):
                height_properties.value = \
                    face_to_be_transformed.longest_length - \
                    height_properties.shoulder_value
                height_properties.percentage = \
                    height_properties.value / \
                    face_to_be_transformed.longest_length

        if height_properties.haunch_type == "percentage":
            height_properties.haunch_depth_value = \
                mortise_properties.depth_value * \
                height_properties.haunch_depth_percentage

        # Check input values
        total_length = height_properties.shoulder_value + \
            height_properties.value
        if ((not nearly_equal(total_length,
                              face_to_be_transformed.longest_length)) and
                (total_length > face_to_be_transformed.longest_length)):
            self.report({'ERROR_INVALID_INPUT'},
                        "Size of length size shoulder and mortise height are "
                        "too long.")
            return {'CANCELLED'}

        total_length = thickness_properties.shoulder_value + \
            thickness_properties.value
        if ((not nearly_equal(total_length,
                              face_to_be_transformed.shortest_length)) and
                (total_length > face_to_be_transformed.shortest_length)):
            self.report({'ERROR_INVALID_INPUT'},
                        "Size of width size shoulder and mortise thickness are "
                        "too long.")
            return {'CANCELLED'}

        # Create mortise
        builder_properties = self.__mortise_properties_to_builder_properties(mortise_properties)
        mortise_builder = TenonMortiseBuilder(
            face_to_be_transformed,
            builder_properties)
        mortise_builder.create(bm, matrix_world)

        # Flush selection
        bm.select_flush_mode()

        if mesh.is_editmode:
            bmesh.update_edit_mesh(mesh)
        else:
            bm.to_mesh(mesh)
            mesh.update()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(MortiseOperator)


def unregister():
    bpy.utils.unregister_class(MortiseOperator)


# ----------------------------------------------
# Code to run the script alone
# ----------------------------------------------
if __name__ == "__main__":
    register()
