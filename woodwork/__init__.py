# add-on info
bl_info = {
    "name": "wood work",
    "description": "Help joining timber for woodworkers",
    "author": "Christophe Chabanois",
    "version": (1, 0),
    "blender": (2, 71, 0),
    "location": "View3D > Tool Shelf > Woodworking",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/Khrisbie/blender-woodworking",
    "category": "Mesh"}

# import files in package
if "bpy" in locals():
    print("Reloading WoodWorking v %d.%d" % bl_info["version"])
    import imp
    imp.reload(tenon_properties)
    imp.reload(tenon)
    imp.reload(main_panel)
    imp.reload(translations)

else:
    print("Loading WoodWorking v %d.%d" % bl_info["version"])
    from . import tenon_properties
    from . import tenon
    from . import main_panel
    from . import translations

# registration
def register():
    tenon_properties.register()
    tenon.register()
    main_panel.register()
    translations.register(__name__)

def unregister():
    tenon_properties.unregister()
    tenon.unregister()
    main_panel.unregister()
    translations.unregister(__name__)

if __name__ == '__main__':
    register()
