# add-on info
bl_info = {
    "name": "wood work",
    "description": "Help joining timber for woodworkers",
    "author": "Christophe Chabanois",
    "version": (1, 0),
    "blender": (2, 71, 0),
    "location": "View3D > Tool Shelf > Woodworking",
    "warning": "",
    "wiki_url": "https://github.com/Khrisbie/blender-woodworking",
    "category": "Mesh"}

# import files in package
if "bpy" in locals():
    print("Reloading WoodWorking v %d.%d" % bl_info["version"])
    import imp
    imp.reload(mortise_properties)
    imp.reload(mortise)
    imp.reload(tenon_properties)
    imp.reload(tenon)
    imp.reload(joints_panel)
    imp.reload(translations)

else:
    print("Loading WoodWorking v %d.%d" % bl_info["version"])
    from . import mortise_properties
    from . import mortise
    from . import tenon_properties
    from . import tenon
    from . import joints_panel
    from . import translations


# registration
def register():
    tenon_properties.register()
    tenon.register()
    mortise_properties.register()
    mortise.register()
    joints_panel.register()
    translations.register(__name__)


def unregister():
    translations.unregister(__name__)
    joints_panel.unregister()
    mortise.unregister()
    mortise_properties.unregister()
    tenon.unregister()
    tenon_properties.unregister()

if __name__ == '__main__':
    register()
