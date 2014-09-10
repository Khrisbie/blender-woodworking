import bpy

class WoodworkingPanel(bpy.types.Panel) :

    bl_label = "Woodworking"
    bl_idname = "woodworking_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_context = "scene"

    def draw(self, context) :
        layout = self.layout

        box = layout.box()
        box.label("Joints", icon='GROUP')
        row = box.row()
        row.operator("mesh.tenon")



def register():
    bpy.utils.register_class(WoodworkingPanel)


def unregister():
    bpy.utils.unregister_class(WoodworkingPanel)

if __name__ == "__main__":
    register()
 


