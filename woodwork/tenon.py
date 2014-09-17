import bpy, bmesh
from mathutils import Vector, Matrix
from math import pi
from mathutils.geometry import (distance_point_to_plane, intersect_point_line)
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


# Get a list of all selected faces
def get_selected_faces(bm):

        return [f for f in bm.faces if f.select]

# is_face_planar
#
# Tests a face to see if it is planar.
def is_face_planar(face, error = 0.0005):
    for v in face.verts:
        d = distance_point_to_plane(v.co, face.verts[0].co, face.normal)
        if bpy.app.debug:
            print("Distance: " + str(d))
        if d < -error or d > error :
            return False
    return True

def is_face_rectangular(face, error = 0.0005):
    for loop in face.loops:
        perp_angle = loop.calc_angle() - (pi / 2)
        if perp_angle < -error or perp_angle > error:
            return False
    return True

def constraint_axis_from_tangent(tangent):
    if tangent[0] == -1.0 or tangent[0] == 1:
        return (True, False, False)
    elif tangent[1] == -1.0 or tangent[1] == 1:
        return (False, True, False)
    return (False, False, True)

def vector_abs(vector) :
    for i in range(len(vector)):
        if (vector[i] < 0.0):
            vector[i] = abs(vector[i])


def nearlyEqual(a, b, epsilon = 0.00001):
    absA = abs(a)
    absB = abs(b)
    diff = abs(a - b)

    if a == b :
        return True
    elif (a == 0.0 or b == 0.0 or diff < float_info.min):
        return diff < (epsilon * float_info.min)
    else :
        return diff / (absA + absB) < epsilon


def zero_element_under_tol(vector, tol = 1e-6):
     for elem in vector:
        if abs(elem) < tol:
            elem = 0

def same_direction(tangent0, tangent1) :
    angle = tangent0.angle(tangent1)

    return nearlyEqual(angle, 0.0) or nearlyEqual(angle, pi)

def distance_point_edge(pt, edge):
    line_p1 = edge.verts[0].co
    line_p2 = edge.verts[1].co
    ret = intersect_point_line(pt, line_p1, line_p2)
    closest_point_on_line = ret[0]
    distance_vector = closest_point_on_line - pt
    return distance_vector.length

class Tenon(bpy.types.Operator):
    bl_description = "Creates a tenon given a face"
    bl_idname = "mesh.tenon"
    bl_label = "Tenon"
    bl_options = {'REGISTER','UNDO'}

    #
    # Class variables
    #

    shortest_length = -1.0
    longest_length = -1.0

    thickness_type = bpy.props.EnumProperty(
        items=[('max',
                "Max. thickness", 
                "Set thickness to the maximum width"),
               ('value', 
                "Value", 
                "Give value to thickness"),
               ('percentage', 
                "Percentage", 
                "Set thickness by percentage")],
        name="Thickness type", 
        default='value')

    thickness_value = bpy.props.FloatProperty(
                    name = "Thickness",
                    description = "Tenon thickness (relative to width side)",
                    min = 0.0,
                    default = -1.0,
                    subtype = 'DISTANCE',
                    unit = 'LENGTH',
                    precision = 3,
                    step = 0.1)

    thickness_percentage = bpy.props.FloatProperty(
                    name = "Thickness",
                    description = "Tenon thickness (relative to width side)",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    thickness_centered = bpy.props.BoolProperty(
                    name = "Centered",
                    description = "Specify if tenon is centered on width side",
                    default = True)

    thickness_shoulder_type = bpy.props.EnumProperty(
        items=[('value', 
                "Value", 
                "Give value to shoulder thickness"),
               ('percentage', 
                "Percentage", 
                "Set thickness shoulder by percentage")],
        name="Thickness shoulder type", 
        default='value')

    thickness_shoulder_value = bpy.props.FloatProperty(
                    name = "Shoulder",
                    description = "Tenon shoulder on width side",
                    min = 0.0,
                    default = -1.0,
                    subtype = 'DISTANCE',
                    unit = 'LENGTH',
                    precision = 3,
                    step = 0.1)

    thickness_shoulder_percentage = bpy.props.FloatProperty(
                    name = "Shoulder",
                    description = "Tenon shoulder (relative to width side)",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    thickness_reverse_shoulder = bpy.props.BoolProperty(
                    name = "Reverse shoulder",
                    description = "Specify shoulder for the other side",
                    default = False)

    height_type = bpy.props.EnumProperty(
        items=[('max', 
                "Max. height", 
                "Set height to the maximum length"),
               ('value', 
                "Value", 
                "Give value to height"),
               ('percentage', 
                "Percentage", 
                "Set height by percentage")],
        name="Height type", 
        default='value')

    height_value = bpy.props.FloatProperty(
                        name = "Height",
                        description = "Tenon height relative to length side",
                        min = 0.0,
                        default = -1.0,
                        subtype = 'DISTANCE',
                        unit ='LENGTH',
                        precision = 3,
                        step = 0.1)

    height_percentage = bpy.props.FloatProperty(
                    name = "Height",
                    description = "Tenon height relative to length side",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    height_centered = bpy.props.BoolProperty(
                    name = "Centered",
                    description = "Specify if tenon is centered on length side",
                    default = True)

    height_shoulder_type = bpy.props.EnumProperty(
        items=[('value', 
                "Value", 
                "Give value to shoulder height"),
               ('percentage', 
                "Percentage", 
                "Set shoulder height by percentage")],
        name="Height shoulder type", 
        default='value')

    height_shoulder_value = bpy.props.FloatProperty(
                    name = "Shoulder",
                    description = "Tenon shoulder on length side",
                    min = 0.0,
                    default = -1.0,
                    subtype = 'DISTANCE',
                    unit = 'LENGTH',
                    precision = 3,
                    step = 0.1)

    height_shoulder_percentage = bpy.props.FloatProperty(
                    name = "Shoulder",
                    description = "Tenon shoulder (relative to length side)",
                    min = 0.0,
                    max = 1.0,
                    subtype = 'PERCENTAGE',
                    unit = 'LENGTH')

    height_reverse_shoulder = bpy.props.BoolProperty(
                    name = "Reverse shoulder",
                    description = "Specify shoulder for the other side",
                    default = False)

    depth_value = bpy.props.FloatProperty(
                        name = "Depth",
                        description = "Tenon depth",
                        min = 0.0,
                        default = -1.0,
                        subtype = 'DISTANCE',
                        unit = 'LENGTH',
                        precision = 3,
                        step = 0.1)

    # Subdivide given edges and return created faces
    def __subdivide_edges(self, bm, edges_to_subdivide):
        ret = bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, cuts=2, use_grid_fill=True)

        # Get the new faces

        # Can't rely on Faces as certain faces are not tagged when only two edges are subdivided
        # see  source / blender / bmesh / operators / bmo_subdivide.c
        #subdivided_faces = [bmesh_type for bmesh_type in ret["geom"] if type(bmesh_type) is bmesh.types.BMFace]
        new_edges = [bmesh_type for bmesh_type in ret["geom_inner"] if type(bmesh_type) is bmesh.types.BMEdge]
        subdivided_faces = set()
        for new_edge in new_edges:
            for linked_face in new_edge.link_faces:
                subdivided_faces.add(linked_face)
        return subdivided_faces

    # Extrude and fatten to set tenon length                 
    def __set_tenon_depth(self, bm, matrix_world, tenon_face):

        ret = bmesh.ops.extrude_discrete_faces(bm, faces=[tenon_face])

        # get only rotation from matrix_world (no scale or translation)
        rot_mat = matrix_world.copy().to_3x3().normalized()

        extruded_face = ret['faces'][0]

        # apply rotation to the normal
        normal_world = rot_mat * extruded_face.normal
        normal_world = normal_world * self.depth_value

        bmesh.ops.translate(bm,  vec=normal_world, space=matrix_world, verts=extruded_face.verts)

        bpy.ops.mesh.select_all(action="DESELECT")
        extruded_face.select = True

    def __resize_faces(self, faces, side_tangent, scale_factor):

        bpy.ops.mesh.select_all(action="DESELECT")
        for faceToResize in faces :
            faceToResize.select = True

        vector_abs(side_tangent)
        resize_value = side_tangent * scale_factor

        bpy.ops.transform.resize(value=resize_value,constraint_axis=constraint_axis_from_tangent(side_tangent), constraint_orientation='LOCAL')

    # Custom layout
    def draw(self, context):
        layout = self.layout

        layout.label(text = "Width side")

        widthSideBox = layout.box()
        widthSideBox.label(text="Thickness type")
        widthSideBox.prop(self, "thickness_type", text = "")
        if self.thickness_type == "value":
            widthSideBox.prop(self, "thickness_value", text = "")
        elif self.thickness_type == "percentage":
            widthSideBox.prop(self, "thickness_percentage", text = "", slider = True)
        widthSideBox.label(text="Position")
        widthSideBox.prop(self, "thickness_centered")
        if self.thickness_centered == False:
            widthSideBox.label(text="Thickness shoulder type")
            widthSideBox.prop(self, "thickness_shoulder_type", text = "")
            if self.thickness_shoulder_type == "value":            
                widthSideBox.prop(self, "thickness_shoulder_value")
            elif self.thickness_shoulder_type == "percentage":
                widthSideBox.prop(self, "thickness_shoulder_percentage", text = "", slider = True)
            widthSideBox.prop(self, "thickness_reverse_shoulder")

        layout.label(text = "Length side")

        lengthSideBox = layout.box()
        lengthSideBox.label(text="Height type")
        lengthSideBox.prop(self, "height_type", text = "")
        if self.height_type == "value" :
            lengthSideBox.prop(self, "height_value", text = "")
        elif self.height_type == "percentage":
            lengthSideBox.prop(self, "height_percentage", text = "", slider = True)
        lengthSideBox.label(text="Position")
        lengthSideBox.prop(self, "height_centered")
        if self.height_centered == False:
            lengthSideBox.label(text="Height shoulder type")
            lengthSideBox.prop(self, "height_shoulder_type", text = "")
            if self.height_shoulder_type == "value" :
                lengthSideBox.prop(self, "height_shoulder_value")
            elif self.height_shoulder_type == "percentage":
                lengthSideBox.prop(self, "height_shoulder_percentage", text = "", slider = True)
            lengthSideBox.prop(self, "height_reverse_shoulder")

        layout.label(text = "Depth")
        layout.prop(self, "depth_value", text = "")


    # used to check if the operator can run
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return(ob and ob.type == 'MESH' and context.mode == 'EDIT_MESH')

    def execute(self, context):

        sce = context.scene
        obj = context.object
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
        if self.thickness_value == -1.0 or (not nearlyEqual(shortest_length, self.shortest_length)) :
            self.thickness_value = shortest_length / 3.0
            self.thickness_percentage = 1.0 / 3.0
        if self.height_value == -1.0 or (not nearlyEqual(longest_length, self.longest_length)) :
            self.height_value = (longest_length * 2.0) / 3.0
            self.height_percentage = 2.0 / 3.0
        if self.depth_value == -1.0 or (not nearlyEqual(longest_length, self.longest_length)) :
            self.depth_value = shortest_length

        self.shortest_length = shortest_length    # used to reinit default values when face changes
        self.longest_length = longest_length

        # If percentage specified, compute length values
        if self.thickness_type == "percentage":
            self.thickness_value = shortest_length * self.thickness_percentage

        if self.height_type == "percentage":
            self.height_value = longest_length * self.height_percentage

        # Init values linked to shoulder size
        if self.thickness_centered == True:
            self.thickness_shoulder_value = (shortest_length - self.thickness_value) / 2.0
            self.thickness_shoulder_percentage = self.thickness_shoulder_value / shortest_length
        if self.height_centered == True:
            self.height_shoulder_value = (longest_length - self.height_value) / 2.0
            self.height_shoulder_percentage = self.height_shoulder_value / longest_length
        
        # If shoulder percentage specified, compute length values
        if self.thickness_shoulder_type == "percentage":
            self.thickness_shoulder_value = shortest_length * self.thickness_shoulder_percentage

        if self.height_shoulder_type == "percentage":
            self.height_shoulder_value = longest_length * self.height_shoulder_percentage

        # Check input values
        if self.height_shoulder_value + self.height_value > longest_length:
            self.report({'ERROR_INVALID_INPUT'},
                        "Size of length size shoulder and tenon height are too long.")
            return {'CANCELLED'}

        if self.thickness_shoulder_value + self.thickness_value > shortest_length:
            self.report({'ERROR_INVALID_INPUT'},
                        "Size of width size shoulder and tenon thickness are too long.")
            return {'CANCELLED'}

        # Subdivide face
        edges_to_subdivide = []
        if self.height_type == "max" and self.height_centered == True:
            # if tenon height set to maximum, select shortest side edges
            # to subdivide only in this direction
            for edge in shortest_edges :
                edges_to_subdivide.append(edge)

        elif self.thickness_type == "max" and self.thickness_centered == True:
            # if tenon thickness set to maximum, select longest side edges
            # to subdivide only in this direction
            for edge in longest_edges :
                edges_to_subdivide.append(edge)
        else:
            edges_to_subdivide=face.edges

        subdivided_faces = self.__subdivide_edges(bm, edges_to_subdivide)

        # Find tenon face (face containing median center)
        for f in subdivided_faces:
            if bmesh.geometry.intersect_face_point(f, median):
              tenon = f
              break

        thicknessFaces = []
        heightFaces = []

        thicknessFaces.append(tenon)
        heightFaces.append(tenon)
        thickness_reference_edge = None
        height_reference_edge = None

        if self.height_type == "max" and self.height_centered == True:
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
        elif self.thickness_type == "max" and self.thickness_centered == True:
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

                                    if height_reference_edge == None:
                                        height_reference_edge = tenonEdge

                                else :
                                    thicknessFaces.append(connectedFace)

                                    if thickness_reference_edge == None:
                                        thickness_reference_edge = tenonEdge

        # Set tenon shoulder on height side
        if self.height_centered == False:

            shoulder = None
            for face in thicknessFaces:
                if face != tenon:
                    if self.height_reverse_shoulder == True:
                        if shoulder != None:
                            shoulder = face
                            height_shoulder_origin_face_edge = shortest_edges[1]  # TODO : take the edge that match shoulder face
                            break
                        else:
                            shoulder = face
                    else:
                        shoulder = face
                        height_shoulder_origin_face_edge = shortest_edges[0] # TODO : take the edge that match shoulder face
                        break

            # find faces to scale
            shoulderFaces = [shoulder]
            height_shoulder_reference_edge = None

            for edge in shoulder.edges:

                connectedFaces = edge.link_faces
                for connectedFace in connectedFaces:

                    if connectedFace != shoulder:
                        connectedLoops = edge.link_loops
                        for connectedLoop in connectedLoops:
                            if connectedLoop.face == shoulder:
                                tangent = edge.calc_tangent(connectedLoop)

                                if same_direction(tangent, longest_side_tangent):
                                    shoulderFaces.append(connectedFace)

                                    if height_shoulder_reference_edge == None:
                                        height_shoulder_reference_edge = edge


            # find vertices to move (those are vertices in both shoulderFaces and heightFaces)
            heightShoulderVerts = set()
            for face in shoulderFaces:
                verts = face.verts
                for vert in verts:
                    heightShoulderVerts.add(vert)
            heightVerts = set()
            for face in heightFaces:
                verts = face.verts
                for vert in verts:
                    heightVerts.add(vert)
            verts_to_translate = heightShoulderVerts.intersection(heightVerts)

            # compute scale factor

            pt1 = height_shoulder_reference_edge.verts[1].co
            pt0 = height_shoulder_reference_edge.verts[0].co

            length1 = distance_point_edge(pt1, height_shoulder_origin_face_edge)
            length0 = distance_point_edge(pt0, height_shoulder_origin_face_edge)
            if (length1 > length0):
                edge_vector = (matrix_world * pt1) - (matrix_world * pt0)
            else:
                edge_vector = (matrix_world * pt0) - (matrix_world * pt1)
            shoulder_length_to_resize = edge_vector.length
            scale_factor = self.height_shoulder_value / shoulder_length_to_resize
            final_vector = edge_vector * scale_factor
            translate_vector = final_vector - edge_vector

            # Slide tenon edge to set the distance between the face border and the tenon
            bmesh.ops.translate(bm, vec=translate_vector, space=matrix_world, verts=list(verts_to_translate))

        # Set tenon shoulder on width side
        if self.thickness_centered == False:

            shoulder = None
            for face in heightFaces:
                if face != tenon:
                    if self.thickness_reverse_shoulder == True:
                        if shoulder != None:
                            shoulder = face
                            thickness_shoulder_origin_face_edge = longest_edges[1]  # TODO : take the edge that match shoulder face
                            break
                        else:
                            shoulder = face
                    else:
                        shoulder = face
                        thickness_shoulder_origin_face_edge = longest_edges[0] # TODO : take the edge that match shoulder face
                        break

            # find faces to scale
            shoulderFaces = [shoulder]
            width_shoulder_reference_edge = None

            for edge in shoulder.edges:

                connectedFaces = edge.link_faces
                for connectedFace in connectedFaces:

                    if connectedFace != shoulder:
                        connectedLoops = edge.link_loops
                        for connectedLoop in connectedLoops:
                            if connectedLoop.face == shoulder:
                                tangent = edge.calc_tangent(connectedLoop)

                                if same_direction(tangent, shortest_side_tangent):
                                    shoulderFaces.append(connectedFace)

                                    if width_shoulder_reference_edge == None:
                                        width_shoulder_reference_edge = edge


            # find vertices to move (those are vertices in both shoulderFaces and thicknessFaces)
            thicknessShoulderVerts = set()
            for face in shoulderFaces:
                verts = face.verts
                for vert in verts:
                    thicknessShoulderVerts.add(vert)
            thicknessVerts = set()
            for face in thicknessFaces:
                verts = face.verts
                for vert in verts:
                    thicknessVerts.add(vert)
            verts_to_translate = thicknessShoulderVerts.intersection(thicknessVerts)

            # compute scale factor

            pt1 = width_shoulder_reference_edge.verts[1].co
            pt0 = width_shoulder_reference_edge.verts[0].co

            length1 = distance_point_edge(pt1, thickness_shoulder_origin_face_edge)
            length0 = distance_point_edge(pt0, thickness_shoulder_origin_face_edge)
            if (length1 > length0):
                edge_vector = (matrix_world * pt1) - (matrix_world * pt0)
            else:
                edge_vector = (matrix_world * pt0) - (matrix_world * pt1)
            shoulder_length_to_resize = edge_vector.length
            scale_factor = self.thickness_shoulder_value / shoulder_length_to_resize
            final_vector = edge_vector * scale_factor
            translate_vector = final_vector - edge_vector

            # Slide tenon edge to set the distance between the face border and the tenon
            bmesh.ops.translate(bm, vec=translate_vector, space=matrix_world, verts=list(verts_to_translate))

        # Set tenon thickness
        if self.thickness_type != "max":
            v0 = thickness_reference_edge.verts[0].co
            v1 = thickness_reference_edge.verts[1].co

            v0_world = matrix_world * v0
            v1_world = matrix_world * v1
            tenonThicknessToResize = (v0_world - v1_world).length
            scale_factor = self.thickness_value / tenonThicknessToResize

            if self.thickness_centered == True:
                # centered
                self.__resize_faces(thicknessFaces, longest_side_tangent, scale_factor)
            else:
                # shouldered
                verts_to_translate = thicknessVerts.difference(thicknessShoulderVerts)

                length1 = distance_point_edge(v1, thickness_shoulder_origin_face_edge)
                length0 = distance_point_edge(v0, thickness_shoulder_origin_face_edge)

                if (length1 > length0):
                    edge_vector = v1_world - v0_world
                else:
                    edge_vector = v0_world - v1_world
                final_vector = edge_vector * scale_factor
                translate_vector = final_vector - edge_vector
                bmesh.ops.translate(bm, vec=translate_vector, space=matrix_world, verts=list(verts_to_translate))


        # Set tenon height
        if self.height_type != "max":

            v0 = height_reference_edge.verts[0].co
            v1 = height_reference_edge.verts[1].co

            v0_world = matrix_world * v0
            v1_world = matrix_world * v1
            tenonHeightToResize = (v0_world - v1_world).length
            scale_factor = self.height_value / tenonHeightToResize

            if self.height_centered == True:
                # centered
                self.__resize_faces(heightFaces, shortest_side_tangent, scale_factor)
            else:
                # shouldered
                verts_to_translate = heightVerts.difference(heightShoulderVerts)

                length1 = distance_point_edge(v1, height_shoulder_origin_face_edge)
                length0 = distance_point_edge(v0, height_shoulder_origin_face_edge)

                if (length1 > length0):
                    edge_vector = v1_world - v0_world
                else:
                    edge_vector = v0_world - v1_world
                final_vector = edge_vector * scale_factor
                translate_vector = final_vector - edge_vector
                bmesh.ops.translate(bm, vec=translate_vector, space=matrix_world, verts=list(verts_to_translate))

        # Set tenon depth
        self.__set_tenon_depth(bm, matrix_world, tenon)

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
