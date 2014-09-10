import bpy, bmesh
from mathutils import Vector, Matrix
from math import pi
from mathutils.geometry import (distance_point_to_plane)
from sys import float_info

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
        if (vector[i] < 0.0) :
            vector[i] = abs(vector[i])


def nearlyEqual(a, b, epsilon = 0.00001) :
    absA = abs(a)
    absB = abs(b)
    diff = abs(a - b)

    if a == b :
        return True
    elif (a == 0.0 or b == 0.0 or diff < float_info.min) :
        return diff < (epsilon * float_info.min)
    else :
        return diff / (absA + absB) < epsilon


def zero_element_under_tol(vector, tol = 1e-6):
     for elem in vector :
        if abs(elem) < tol :
            elem = 0

def same_direction(tangent0, tangent1) :
    angle = tangent0.angle(tangent1)

    return nearlyEqual(angle, 0.0) or nearlyEqual(angle, pi)
    
class Tenon(bpy.types.Operator):
    bl_description = "Creates a tenon given a face"
    bl_idname = "mesh.tenon"
    bl_label = "Tenon"
    bl_options = {'REGISTER','UNDO'}
    
    shortest_length = -1.0
    longest_length = -1.0

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
                                        step = 0.1)

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
        
        matrix_world = obj.matrix_world
        v0 = matrix_world * e0.verts[0].co
        v1 = matrix_world * e0.verts[1].co
        length0 = (v0 - v1).length
        v0 = matrix_world * e1.verts[0].co
        v1 = matrix_world * e1.verts[1].co
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
        
        # Init default values, look if face has changed too
        if self.thickness == -1 or (not nearlyEqual(shortest_length, self.shortest_length)) :
            self.thickness = shortest_length / 3.0
        if self.height == -1 or (not nearlyEqual(longest_length, self.longest_length)) :
            self.height = (longest_length * 2.0) / 3.0
        if self.depth == -1 or (not nearlyEqual(longest_length, self.longest_length)) :
            self.depth = longest_length
        
        self.shortest_length = shortest_length    # used to reinit default values when face changes
        self.longest_length = longest_length

        # Subdivide face
        edges_to_subdivide = []
        if self.height_type == "max" :
            # if tenon height set to maximum, select shortest side edges
            # to subdivide only in this direction
            for edge in shortest_edges :
                edges_to_subdivide.append(edge)
        elif self.thickness_type == "max" :
            # if tenon thickness set to maximum, select longest side edges
            # to subdivide only in this direction
            for edge in longest_edges :
                edges_to_subdivide.append(edge)
        else :
            edges_to_subdivide=face.edges

        ret = bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, cuts=2, use_grid_fill=True)
            
        # Get the new faces
        subdivided_faces = [bmesh_type for bmesh_type in ret["geom_inner"] if type(bmesh_type) is bmesh.types.BMFace]
        
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
            
            if same_direction(tangent0, shortest_side_tangent) :
                v0 = matrix_world * e0.verts[0].co
                v1 = matrix_world * e0.verts[1].co
            else :
                v0 = matrix_world * e1.verts[0].co
                v1 = matrix_world * e1.verts[1].co
            tenonThicknessToResize = (v0 - v1).length
        elif self.thickness_type == "max" :
            # get tenon side facing the longest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge
            
            tangent0 = e0.calc_tangent(l0)
            
            if same_direction(tangent0, longest_side_tangent) :
                v0 = matrix_world * e0.verts[0].co
                v1 = matrix_world * e0.verts[1].co
            else :
                v0 = matrix_world * e1.verts[0].co
                v1 = matrix_world * e1.verts[1].co
            tenonHeightToResize = (v0 - v1).length
        else :
            # Find faces to resize to obtain tenon base
            tenonEdges = tenon.edges
            for tenonEdge in tenonEdges:
                connectedFaces = tenonEdge.link_faces
                for connectedFace in connectedFaces:
                    if connectedFace != tenon:
                        connectedLoops = tenonEdge.link_loops
                        for connectedLoop in connectedLoops:
                            if connectedLoop.face == connectedFace:
                                # Return the tangent at this edge relative to a face (pointing inward into the face).
                                # This uses the face normal for calculation.
                                tangent = tenonEdge.calc_tangent(connectedLoop)

                                if same_direction(tangent,longest_side_tangent) :
                                    heightFaces.append(connectedFace)
                                    
                                    v0 = matrix_world * tenonEdge.verts[0].co
                                    v1 = matrix_world * tenonEdge.verts[1].co
                                    tenonHeightToResize = (v0 - v1).length
                                else :
                                    thicknessFaces.append(connectedFace)
                                    
                                    v0 = matrix_world * tenonEdge.verts[0].co
                                    v1 = matrix_world * tenonEdge.verts[1].co
                                    tenonThicknessToResize = (v0 - v1).length

        # Set tenon thickness
        if self.thickness_type != "max" :
            bpy.ops.mesh.select_all(action="DESELECT")
            for faceToResize in thicknessFaces :
                faceToResize.select = True
            vector_abs(longest_side_tangent)
            scale_factor = self.thickness / tenonThicknessToResize
            resize_value = longest_side_tangent * scale_factor

            bpy.ops.transform.resize(value=resize_value,constraint_axis=constraint_axis_from_tangent(longest_side_tangent), constraint_orientation='LOCAL')

        # Set tenon height
        if self.height_type != "max" :
            bpy.ops.mesh.select_all(action="DESELECT")
            for faceToResize in heightFaces :
                faceToResize.select = True
            vector_abs(shortest_side_tangent)
            scale_factor = self.height / tenonHeightToResize
            resize_value = shortest_side_tangent * scale_factor

            bpy.ops.transform.resize(value=resize_value,constraint_axis=constraint_axis_from_tangent(shortest_side_tangent), constraint_orientation='LOCAL')

        # Extrude and fatten to set tenon length
        ret = bmesh.ops.extrude_discrete_faces(bm, faces=[tenon])
        
        # get only rotation from matrix_world (no scale or translation)
        rot_mat = matrix_world.copy().to_3x3().normalized()
       
        extruded_face = ret['faces'][0]

        # apply rotation to the normal
        normal_world = rot_mat * extruded_face.normal
        normal_world = normal_world * self.depth

        bmesh.ops.translate(bm,  vec=normal_world, space=matrix_world, verts=extruded_face.verts)
        
        bpy.ops.mesh.select_all(action="DESELECT")
        extruded_face.select = True
  
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







