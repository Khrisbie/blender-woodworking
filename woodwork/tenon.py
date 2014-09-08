import bpy, bmesh, mathutils
from math import pi
from mathutils.geometry import (distance_point_to_plane)

# See if the current item should be selected or not
def selectCheck(isSelected, hasSelected, extend):
               
        # If we are extending or nothing is selected we want to select
        if extend or not hasSelected:
                return True
                       
        return False



# See if the current item should be deselected or not
def deselectCheck(isSelected, hasSelected, extend):
       
        # If something is selected and we're not extending we want to deselect
        if hasSelected and not extend:
                return True

        return False

# See if there is at least one selected item in 'items'
def contains_selected_item(items):

        for item in items:
                if item.select:
                        return True
                               
        return False

# Select by direction
def by_direction(direction, divergence, extend=False):
       
        mesh = bpy.context.active_object.data
        direction = mathutils.Vector(direction)
       
        hasSelected = contains_selected_item(mesh.faces)
       
        # Make sure there's an actual directions
        if direction.length:

                # Loop through all the given faces
                for f in mesh.faces:
               
                        isSelected = f.select
                        s = selectCheck(isSelected, hasSelected, extend)
                        d = deselectCheck(isSelected, hasSelected, extend)
                       
                        angle = direction.angle(f.normal)
                       
                        if s and angle <= divergence:
                                f.select = True
                        elif d and angle > divergence:
                                f.select = False
# Get the bmesh data from the current mesh object
def get_bmesh():
       
        # Get the active mesh
        ob = bpy.context.active_object
        me = ob.data

        # Get a BMesh representation
        if ob.mode == 'OBJECT':
                bm = bmesh.new()
                bm.from_mesh(me)   # fill it in from a Mesh
        else:
                bm = bmesh.from_edit_mesh(me) # Fill it from edit mode mesh
       
        return bm
       
       
       
# Put the bmesh data back into the current mesh object
def put_bmesh(bm):
       
        # Get the active mesh
        ob = bpy.context.active_object
        me = ob.data
       
        # Flush selection
        bm.select_flush_mode()
       
        # Finish up, write the bmesh back to the mesh
        if ob.mode == 'OBJECT':
                bm.to_mesh(me)
                bm.free()
        else:
                bmesh.update_edit_mesh(me, True)
               
               
               
               
# Get a list of all selected faces
def get_selected_faces(bm):
               
        return [f for f in bm.faces if f.select]

# is_face_planar
#
# Tests a face to see if it is planar.
def is_face_planar(face, error = 0.0005) :
    for v in face.verts:
        d = distance_point_to_plane(v.co, face.verts[0].co, face.normal)
        if bpy.app.debug:
            print("Distance: " + str(d))
        if d < -error or d > error :
            return False
    return True

def is_face_rectangular(face, error = 0.0005) :
    for loop in face.loops:
        perp_angle = loop.calc_angle() - (pi / 2)
        if perp_angle < -error or perp_angle > error:
            print("loop angle = ", loop.calc_angle())
            print("perp_angle = ", perp_angle)
            return False
    return True

def constraint_axis_from_tangent(tangent) :
    if tangent[0] == -1.0 or tangent[0] == 1 :
        return (True, False, False)
    elif tangent[1] == -1.0 or tangent[1] == 1 :
        return (False, True, False)
    return (False, False, True)

def vector_abs(vector) :
    for i in range(len(vector)) : 
        if (vector[i] < 0) :
            vector[i] = abs(vector[i])

class Tenon(bpy.types.Operator):
    bl_description = "Creates a tenon given a face"
    bl_idname = "mesh.tenon"
    bl_label = "Tenon"
    bl_options = {'REGISTER','UNDO'}

    thickness_type = bpy.props.EnumProperty(
        items=[('max', "Max. thickness", "Set thickness to the maximum (length of the shortest side)"),
               ('thickness_value', "Value", "Give value to thickness")],
        name="Thickness type", default='thickness_value')                             
    thickness = bpy.props.FloatProperty(name = "Thickness",
                                        description = "Tenon thickness relative to smallest side",
                                        min = 0.0,
                                        default = -1,
                                        subtype = 'DISTANCE',
                                        unit = 'LENGTH',
                                        precision = 3,
                                        step = 0.01)

    height_type = bpy.props.EnumProperty(
        items=[('max', "Max. height", "Set height to the maximum (length of the biggest side)"),
               ('height_value', "Value", "Give value to height")],
        name="Height type", default='height_value')
                                                
    height = bpy.props.FloatProperty(name = "Height",
                                        description = "Tenon height relative to biggest side",
                                        min = 0.0,
                                        default = -1,
                                        subtype = 'DISTANCE',
                                        unit ='LENGTH',
                                        precision = 3,
                                        step = 0.1)

    depth = bpy.props.FloatProperty(name = "Depth",
                          description = "Tenon depth",
                          min = 0.0,
                          default = -1,
                          subtype = 'DISTANCE',
                          unit = 'LENGTH',
                          precision = 3,
                          step = 0.1)

    def draw(self, context):
        layout = self.layout

        thicknessBox = layout.box()
        thicknessBox.prop(self, "thickness_type")
        if self.thickness_type == "thickness_value" :
            thicknessBox.prop(self, "thickness")
        
        heightBox = layout.box()
        heightBox.prop(self, "height_type")
        if self.height_type == "height_value" :
            heightBox.prop(self, "height")
        layout.prop(self, "depth")


    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return(ob and ob.type == 'MESH' and context.mode == 'EDIT_MESH')

    def execute(self, context):
        
        sce = context.scene
        obj = context.object
        mesh = obj.data
        
        if mesh.is_editmode:
            print("In edit mode")
            # Gain direct access to the mesh
            bm = bmesh.from_edit_mesh(mesh)
        else:
            print("In object mode")
            # Create a bmesh from mesh
            # (won't affect mesh, unless explicitly written back)
            bm = bmesh.new()
            bm.from_mesh(mesh)

        # Get active face
        faces = bm.faces
        face = faces.active

        # If we don't find a selected face, we have problem.  Exit:
        if face == None:
            self.report({'ERROR_INVALID_INPUT'},
                        "You must select a face for the tenon.")
            return {'CANCELLED'}
          
        # Warn the user if face is not 4 vertices.
        if len(face.verts) > 4 :
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is not quad.")
            return {'CANCELLED'}

        
        if not is_face_planar(face) :
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is planar.")
            return {'CANCELLED'}
        
        if not is_face_rectangular(face):
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is not rectangular.")
            return {'CANCELLED'}
        # Get center                
        median = face.calc_center_median()
        
        # Get largest and smallest edge to find resize axes
        l0 = face.loops[0]
        e0 = l0.edge
        l1 = face.loops[1]
        e1 = l1.edge
        
        mat = obj.matrix_world
        v0 = mat * e0.verts[0].co
        v1 = mat * e0.verts[1].co
        length0 = (v0 - v1).length
        v0 = mat * e1.verts[0].co
        v1 = mat * e1.verts[1].co
        length1 = (v0 - v1).length        
        
        if (length0 > length1) :
            longest_side_tangent = e0.calc_tangent(l0)
            shortest_side_tangent = e1.calc_tangent(l1)
            longest_edges=[e0, face.loops[2].edge]
            shortest_edges=[e1, face.loops[3].edge]
            shortest_length = length1
            longest_length = length0
        else :
            longest_side_tangent = e1.calc_tangent(l1)
            shortest_side_tangent = e0.calc_tangent(l0)
            longest_edges=[e1, face.loops[3].edge]
            shortest_edges=[e0, face.loops[2].edge]
            shortest_length = length0
            longest_length = length1
        
        # Initialisation des valeurs par defaut
        # TODO : tenir compte du changement de face (si dimensions differentes)    
        if self.thickness == -1 :
            self.thickness = shortest_length / 3.0
        if self.height == -1 :
            self.height = (longest_length * 2.0) / 3.0
        if self.depth == -1 :
            self.depth = longest_length

        # Subdivide face
        if self.height_type == "max" :
            bpy.ops.mesh.select_all(action="DESELECT")
            # if tenon height set to maximum, select shortest side edges
            # to subdivide only in this direction
            for edge in shortest_edges :
                edge.select = True
        elif self.thickness_type == "max" :
            bpy.ops.mesh.select_all(action="DESELECT")
            # if tenon thickness set to maximum, select longest side edges
            # to subdivide only in this direction
            for edge in longest_edges :
                edge.select = True

        bpy.ops.mesh.subdivide(number_cuts=2)
        
        # Get the new faces   
        subdivided_faces = [f for f in faces if f.select]   # list comprehension
        
        # Find tenon face (face containing median center)
        for f in subdivided_faces:
            if bmesh.geometry.intersect_face_point(f, median):
              tenon = f
              break
          
        thicknessFaces = []
        heightFaces = []
        
        thicknessFaces.append(tenon)
        heightFaces.append(tenon)
        
        if self.height_type == "max" :
            # get tenon side facing the smallest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge
            
            tangent0 = e0.calc_tangent(l0)
            
            if tangent0 == shortest_side_tangent or tangent0 == -shortest_side_tangent :
                v0 = mat * e0.verts[0].co
                v1 = mat * e0.verts[1].co
            else :
                v0 = mat * e1.verts[0].co
                v1 = mat * e1.verts[1].co
            tenonThicknessToResize = (v0 - v1).length
        elif self.thickness_type == "max" :
            # get tenon side facing the longest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge
            
            tangent0 = e0.calc_tangent(l0)
            
            if tangent0 == longest_side_tangent or tangent0 == -longest_side_tangent :
                v0 = mat * e0.verts[0].co
                v1 = mat * e0.verts[1].co
            else :
                v0 = mat * e1.verts[0].co
                v1 = mat * e1.verts[1].co
            tenonHeightToResize = (v0 - v1).length
        else :
            # Find faces to resize to obtain tenon base
            tenonEdges = tenon.edges
            for tenonEdge in tenonEdges:
                connectedFaces = tenonEdge.link_faces
                for connectedFace in connectedFaces:
                    if connectedFace != tenon:
                        print("Found connected face with index ", connectedFace.index)
                        connectedLoops = tenonEdge.link_loops
                        for connectedLoop in connectedLoops:
                            if connectedLoop.face == connectedFace:
                                # Return the tangent at this edge relative to a face (pointing inward into the face).
                                # This uses the face normal for calculation.
                                tangent = tenonEdge.calc_tangent(connectedLoop)
                                print("tangent (edge/connected face) = ", tangent)

                                if tangent == longest_side_tangent or tangent == -longest_side_tangent :
                                    heightFaces.append(connectedFace)
                                    
                                    v0 = mat * tenonEdge.verts[0].co
                                    v1 = mat * tenonEdge.verts[1].co
                                    tenonHeightToResize = (v0 - v1).length
                                else :
                                    thicknessFaces.append(connectedFace)
                                    
                                    v0 = mat * tenonEdge.verts[0].co
                                    v1 = mat * tenonEdge.verts[1].co
                                    tenonThicknessToResize = (v0 - v1).length

        # Set tenon thickness
        if self.thickness_type != "max" :
            bpy.ops.mesh.select_all(action="DESELECT")
            for faceToResize in thicknessFaces :
                faceToResize.select = True
            vector_abs(longest_side_tangent)
            scale_factor = self.thickness / tenonThicknessToResize
            resize_value = longest_side_tangent * scale_factor
            print("resize_value=", resize_value)
            print("constraint_axis=", constraint_axis_from_tangent(longest_side_tangent))
            bpy.ops.transform.resize(value=resize_value,constraint_axis=constraint_axis_from_tangent(longest_side_tangent), constraint_orientation='LOCAL')

        # Set tenon height
        if self.height_type != "max" :
            bpy.ops.mesh.select_all(action="DESELECT")
            for faceToResize in heightFaces :
                faceToResize.select = True
            vector_abs(shortest_side_tangent)
            scale_factor = self.height / tenonHeightToResize
            resize_value = shortest_side_tangent * scale_factor
            print("resize_value=", resize_value)
            print("constraint_axis=", constraint_axis_from_tangent(shortest_side_tangent))
            bpy.ops.transform.resize(value=resize_value,constraint_axis=constraint_axis_from_tangent(shortest_side_tangent), constraint_orientation='LOCAL')

        # Extrude to set tenon length
        bpy.ops.mesh.select_all(action="DESELECT")
        tenon.select = True
        ###### WRONG: SHOULD TAKE GLOBAL TRANSFORM INTO ACCOUNT
        bpy.ops.mesh.extrude_faces_move(TRANSFORM_OT_shrink_fatten={"value":-self.depth})
        
        # Flush selection
        bm.select_flush_mode()
        
        if mesh.is_editmode:
          bmesh.update_edit_mesh(mesh)
        else:
          bm.to_mesh(mesh)
          mesh.update()


        #bm.free()
        #del bm
            
        return {'FINISHED'}

def register():
    bpy.utils.register_class(Tenon)

def unregister():
    bpy.utils.unregister_class(Tenon)


#----------------------------------------------
# Code to run the script alone
#----------------------------------------------
if __name__ == "__main__":
    register()
    print("Executed")







