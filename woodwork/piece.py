import bpy


class WorkpieceOperator(bpy.types.Operator):
    bl_description = "Creates a new workpiece"
    bl_idname = "mesh.woodwork_workpiece"
    bl_label = "Workpiece"
    bl_category = 'Woodwork'
    bl_options = {'REGISTER', 'UNDO'}

    #
    # Class variables
    #
    expand_size_properties = bpy.props.BoolProperty(name="Expand",
                                                    default=True)
    expand_position_properties = bpy.props.BoolProperty(name="Expand",
                                                        default=True)

    def execute(self, context):
        if bpy.context.mode == "OBJECT":

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

        piece_properties = context.scene.woodwork.piece_properties
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
