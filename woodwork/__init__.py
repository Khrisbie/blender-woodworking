# add-on info
bl_info = {
    "name": "wood work",
    "description": "Help joining timber for woodworkers",
    "author": "Christophe Chabanois",
    "version": (1, 0),
    "blender": (2, 71, 0),
    "location": "View3D > Add > Mesh",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
                "Scripts/My_Script",
    "category": "Mesh"}

# import files in package
if "bpy" in locals():
    import imp
    imp.reload(tenon)
    print("Reloaded multifiles")
else:
    from . import tenon
    print("Imported multifiles")

# registration
def register():
    tenon.register()
  
def unregister():
    tenon.unregister()