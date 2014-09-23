import bpy, bmesh
from mathutils import Vector, Matrix
from math import pi
from mathutils.geometry import (distance_point_to_plane, intersect_point_line)
from sys import float_info

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

# This describes the initial face where the tenon will be created
class FaceToBeTransformed:
    def __init__(self, face):
        self.face = face

        self.median = None
        self.longest_side_tangent = None
        self.shortest_side_tangent = None
        self.longest_edges = None
        self.shortest_edges = None
        self.shortest_length = None
        self.longest_length = None

    def extract_features(self, matrix_world):
        face = self.face

        # Get center
        self.median = face.calc_center_median()

        # Get largest and smallest edge to find resize axes
        l0 = face.loops[0]
        e0 = l0.edge
        l1 = face.loops[1]
        e1 = l1.edge

        v0 = matrix_world * e0.verts[0].co
        v1 = matrix_world * e0.verts[1].co
        length0 = (v0 - v1).length
        v0 = matrix_world * e1.verts[0].co
        v1 = matrix_world * e1.verts[1].co
        length1 = (v0 - v1).length

        if (length0 > length1) :
            self.longest_side_tangent = e0.calc_tangent(l0)
            self.shortest_side_tangent = e1.calc_tangent(l1)
            self.longest_edges=[e0, face.loops[2].edge]
            self.shortest_edges=[e1, face.loops[3].edge]
            self.shortest_length = length1
            self.longest_length = length0
        else :
            self.longest_side_tangent = e1.calc_tangent(l1)
            self.shortest_side_tangent = e0.calc_tangent(l0)
            self.longest_edges=[e1, face.loops[3].edge]
            self.shortest_edges=[e0, face.loops[2].edge]
            self.shortest_length = length0
            self.longest_length = length1

    # Subdivide given edges and return created faces
    def __subdivide_edges(self, bm, edges_to_subdivide):
        ret = bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, cuts=2, use_grid_fill=True)

        # Get the new faces

        # Can't rely on Faces as certain faces are not tagged when only two edges are subdivided
        # see  source / blender / bmesh / operators / bmo_subdivide.c
        #subdivided_faces = [bmesh_type for bmesh_type in ret["geom"] if type(bmesh_type) is bmesh.types.BMFace]
        new_edges = [bmesh_type for bmesh_type in ret["geom_inner"] if type(bmesh_type) is bmesh.types.BMEdge]
        del ret
        subdivided_faces = set()
        for new_edge in new_edges:
            for linked_face in new_edge.link_faces:
                subdivided_faces.add(linked_face)
        return subdivided_faces

    # Subdivide face to be transformed to a tenon
    def subdivide_face(self, bm, heightProperties, thicknessProperties):
        edges_to_subdivide = []

        max_centered_height = bool(heightProperties.type == "max" and heightProperties.centered == True)
        max_centered_thickness = bool(thicknessProperties.type == "max" and thicknessProperties.centered == True)

        if max_centered_height and not max_centered_thickness:
            # if tenon height set to maximum, select shortest side edges
            # to subdivide only in this direction
            for edge in self.shortest_edges :
                edges_to_subdivide.append(edge)

        elif max_centered_thickness and not max_centered_height:
            # if tenon thickness set to maximum, select longest side edges
            # to subdivide only in this direction
            for edge in self.longest_edges :
                edges_to_subdivide.append(edge)

        elif not (max_centered_height and max_centered_thickness):
            edges_to_subdivide=self.face.edges

        return self.__subdivide_edges(bm, edges_to_subdivide)

# This structure keep info about the newly created tenon face
class TenonFace:
    def __init__(self, face):
        self.face = face
        self.thickness_faces = []
        self.height_faces = []
        self.thickness_reference_edge = None
        self.height_reference_edge = None

    # find tenon adjacent faces to be translated or resized given user's values
    # - height_faces[] are the faces which follows the direction of the longest side
    # - thickness_faces[] are the faces which follows the direction of the shortest side
    # - thickness_reference_edge and height_reference_edge are tenon edges used
    #   to determine scale factor
    def find_adjacent_faces(self, faceToBeTransformed, heightProperties, thicknessProperties):
        tenon = self.face

        self.thickness_faces.append(tenon)
        self.height_faces.append(tenon)

        # Find faces to resize to obtain tenon base
        tenonEdges = tenon.edges
        for tenonEdge in tenonEdges:
            connectedFaces = tenonEdge.link_faces
            for connectedFace in connectedFaces:
                if connectedFace != tenon:
                    # Found face adjacent to tenon
                    connectedLoops = tenonEdge.link_loops
                    for connectedLoop in connectedLoops:
                        if connectedLoop.face == connectedFace:
                            # Return the tangent at this edge relative to a face (pointing inward into the face).
                            tangent = tenonEdge.calc_tangent(connectedLoop)

                            if same_direction(tangent, faceToBeTransformed.longest_side_tangent) :
                                self.height_faces.append(connectedFace)

                                if self.height_reference_edge == None:
                                    self.height_reference_edge = tenonEdge
                            else :
                                self.thickness_faces.append(connectedFace)

                                if self.thickness_reference_edge == None:
                                    self.thickness_reference_edge = tenonEdge

        if heightProperties.type == "max" and heightProperties.centered == True:
            # get tenon side facing the smallest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge

            tangent0 = e0.calc_tangent(l0)

            if same_direction(tangent0, faceToBeTransformed.shortest_side_tangent) :
                self.thickness_reference_edge = e0
            else :
                self.thickness_reference_edge = e1

        elif thicknessProperties.type == "max" and thicknessProperties.centered == True:
            # get tenon side facing the longest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge

            tangent0 = e0.calc_tangent(l0)

            if same_direction(tangent0, faceToBeTransformed.longest_side_tangent) :
                self.height_reference_edge = e0
            else :
                self.height_reference_edge = e1

    def get_scale_factor(self, reference_edge, matrix_world, resize_value):
        v0 = reference_edge.verts[0].co
        v1 = reference_edge.verts[1].co

        v0_world = matrix_world * v0
        v1_world = matrix_world * v1

        to_be_resized = (v0_world - v1_world).length

        return resize_value / to_be_resized

    def compute_translation_vector_given_shoulder(self, reference_edge, shoulder, scale_factor, matrix_world):

        v0 = reference_edge.verts[0].co
        v1 = reference_edge.verts[1].co

        v0_world = matrix_world * v0
        v1_world = matrix_world * v1

        length1 = distance_point_edge(v1, shoulder.origin_face_edge)
        length0 = distance_point_edge(v0, shoulder.origin_face_edge)

        if (length1 > length0):
            edge_vector = v1_world - v0_world
        else:
            edge_vector = v0_world - v1_world
        final_vector = edge_vector * scale_factor

        return final_vector - edge_vector

    def find_verts_to_translate(self, tenon_faces, shoulder_verts):
        tenon_verts = set()
        for face in tenon_faces:
            verts = face.verts
            for vert in verts:
                tenon_verts.add(vert)

        return tenon_verts.difference(shoulder_verts)

# This describes a shoulder adjacent to the tenon face
class ShoulderFace:
    def __init__(self):
        self.face = None
        self.reference_edge = None
        self.origin_face_edge = None

    # gets the shoulder : it's a face in tenon_adjacent_faces that is not the tenon itself
    def get_from_tenon(self, tenon, tenon_adjacent_faces, reverse_shoulder, origin_face_edges):
        for face in tenon_adjacent_faces:
            if face != tenon.face:
                if reverse_shoulder == True:
                    if self.face != None:
                        self.face = face
                        self.origin_face_edge = origin_face_edges[1]  # TODO : take the edge that match shoulder face
                        break
                    else:
                        self.face = face
                else:
                    self.face = face
                    self.origin_face_edge = origin_face_edges[0] # TODO : take the edge that match shoulder face
                    break

    def find_verts_to_translate(self, origin_face_tangent, tenon_faces):

        # find faces to scale
        shoulder_face = self.face
        shoulder_faces = [shoulder_face]

        for edge in shoulder_face.edges:
            connectedFaces = edge.link_faces

            for connectedFace in connectedFaces:
                if connectedFace != shoulder_face:
                    connectedLoops = edge.link_loops

                    for connectedLoop in connectedLoops:
                        if connectedLoop.face == shoulder_face:
                            tangent = edge.calc_tangent(connectedLoop)

                            if same_direction(tangent, origin_face_tangent):
                                shoulder_faces.append(connectedFace)

                                if self.reference_edge == None:
                                    self.reference_edge = edge

        # when height or thickness set to the max and tenon is centered, this could happen...
        if self.reference_edge == None:
            l0 = shoulder_face.loops[0]
            e0 = l0.edge
            l1 = shoulder_face.loops[1]
            e1 = l1.edge

            tangent0 = e0.calc_tangent(l0)

            if same_direction(tangent0, origin_face_tangent) :
                self.reference_edge = e0
            else :
                self.reference_edge = e1

        # find vertices to move
        shoulder_verts = set()
        for face in shoulder_faces:
            verts = face.verts
            for vert in verts:
                shoulder_verts.add(vert)
        tenon_verts = set()
        for face in tenon_faces:
            verts = face.verts
            for vert in verts:
                tenon_verts.add(vert)
        return shoulder_verts.intersection(tenon_verts)

    def compute_translation_vector(self, shoulder_value, matrix_world):
        # compute scale factor
        pt1 = self.reference_edge.verts[1].co
        pt0 = self.reference_edge.verts[0].co

        length1 = distance_point_edge(pt1, self.origin_face_edge)
        length0 = distance_point_edge(pt0, self.origin_face_edge)
        if (length1 > length0):
            edge_vector = (matrix_world * pt1) - (matrix_world * pt0)
        else:
            edge_vector = (matrix_world * pt0) - (matrix_world * pt1)
        shoulder_length_to_resize = edge_vector.length
        scale_factor = shoulder_value / shoulder_length_to_resize
        final_vector = edge_vector * scale_factor
        return final_vector - edge_vector

class TenonCreator:
    def __init__(self, face_to_be_transformed):
        self.face_to_be_transformed = face_to_be_transformed

    # Extrude and fatten to set face length
    def __set_face_depth(self, depth, bm, matrix_world, face):

        ret = bmesh.ops.extrude_discrete_faces(bm, faces=[face])

        extruded_face = ret['faces'][0]
        del ret

        # apply rotation to the normal
        rot_mat = matrix_world.copy().to_3x3().normalized()
        normal_world = rot_mat * extruded_face.normal
        normal_world = normal_world * depth

        bmesh.ops.translate(bm, vec = normal_world, space = matrix_world, verts = extruded_face.verts)

        bpy.ops.mesh.select_all(action="DESELECT")
        extruded_face.select = True

    # Extrude and translate an edge of the face to set it sloped
    def __set_face_sloped(self,
                          depth,
                          bm,
                          matrix_world,
                          face, 
                          still_edge_tangent):

        # Extrude face
        ret = bmesh.ops.extrude_discrete_faces(bm, faces = [face])

        extruded_face = ret['faces'][0]
        del ret

        # apply rotation to the normal
        rot_mat = matrix_world.copy().to_3x3().normalized()
        normal_world = rot_mat * extruded_face.normal
        normal_world = normal_world * depth

        # Find vertices to be translated
        verts_to_translate = []

        for edge in extruded_face.edges:
            for loop in edge.link_loops:
                if loop.face == extruded_face:
                    tangent = edge.calc_tangent(loop)
                    angle = tangent.angle(still_edge_tangent)
                    if nearlyEqual(angle, pi):
                        for vert in edge.verts:
                            verts_to_translate.append(vert)
                        break
                if len(verts_to_translate) > 0:
                  break
            if len(verts_to_translate) > 0:
              break

        bmesh.ops.translate(bm,
                            vec = normal_world,
                            space = matrix_world,
                            verts = verts_to_translate)

    # resize centered faces
    # TODO: use bmesh instead of bpy.ops
    def __resize_faces(self, faces, side_tangent, scale_factor):

        bpy.ops.mesh.select_all(action="DESELECT")
        for faceToResize in faces :
            faceToResize.select = True

        vector_abs(side_tangent)
        resize_value = side_tangent * scale_factor

        bpy.ops.transform.resize(value=resize_value,constraint_axis=constraint_axis_from_tangent(side_tangent), constraint_orientation='LOCAL')

    def create(self, bm, matrix_world, tenon_properties):
        face_to_be_transformed = self.face_to_be_transformed
        thickness_properties = tenon_properties.thickness_properties
        height_properties = tenon_properties.height_properties

        # Subdivide face
        subdivided_faces = face_to_be_transformed.subdivide_face(bm, height_properties, thickness_properties)

        # Find tenon face (face containing median center)
        if len(subdivided_faces) == 0:
            # when max height centered and max thickness centered (stupid choice but should handle this case too...)
            tenon = TenonFace(face_to_be_transformed.face)

        for f in subdivided_faces:
            if bmesh.geometry.intersect_face_point(f, face_to_be_transformed.median):
              tenon = TenonFace(f)
              break

        # Find faces to be resized
        tenon.find_adjacent_faces(face_to_be_transformed, height_properties, thickness_properties)

        # Set tenon shoulder on height side
        if height_properties.centered == False:

            height_shoulder = ShoulderFace()
            height_shoulder.get_from_tenon(tenon, tenon.thickness_faces, height_properties.reverse_shoulder, face_to_be_transformed.shortest_edges)
            height_shoulder_verts_to_translate = height_shoulder.find_verts_to_translate(face_to_be_transformed.longest_side_tangent, tenon.height_faces)
            translate_vector = height_shoulder.compute_translation_vector(height_properties.shoulder_value, matrix_world)

            bmesh.ops.translate(bm, vec = translate_vector, space = matrix_world, verts = list(height_shoulder_verts_to_translate))

        # Set tenon shoulder on width side
        if thickness_properties.centered == False:

            thickness_shoulder = ShoulderFace()
            thickness_shoulder.get_from_tenon(tenon, tenon.height_faces, thickness_properties.reverse_shoulder, face_to_be_transformed.longest_edges)
            thickness_shoulder_verts_to_translate = thickness_shoulder.find_verts_to_translate(face_to_be_transformed.shortest_side_tangent, tenon.thickness_faces)
            translate_vector = thickness_shoulder.compute_translation_vector(thickness_properties.shoulder_value, matrix_world)

            bmesh.ops.translate(bm, vec=translate_vector, space=matrix_world, verts=list(thickness_shoulder_verts_to_translate))

        # Set tenon thickness
        if thickness_properties.type != "max":
            scale_factor = tenon.get_scale_factor(tenon.thickness_reference_edge, matrix_world, thickness_properties.value)

            if thickness_properties.centered == True:
                # centered
                self.__resize_faces(tenon.thickness_faces, face_to_be_transformed.longest_side_tangent, scale_factor)
            else:
                # shouldered
                verts_to_translate = tenon.find_verts_to_translate(tenon.thickness_faces, thickness_shoulder_verts_to_translate)

                translate_vector = tenon.compute_translation_vector_given_shoulder(
                    tenon.thickness_reference_edge, thickness_shoulder, scale_factor, matrix_world)

                bmesh.ops.translate(bm, vec = translate_vector, space = matrix_world, verts = list(verts_to_translate))


        # Set tenon height
        if height_properties.type != "max":
            scale_factor = tenon.get_scale_factor(tenon.height_reference_edge, matrix_world, height_properties.value)

            if height_properties.centered == True:
                # centered
                self.__resize_faces(tenon.height_faces, face_to_be_transformed.shortest_side_tangent, scale_factor)
            else:
                # shouldered
                verts_to_translate = tenon.find_verts_to_translate(tenon.height_faces, height_shoulder_verts_to_translate)

                translate_vector = tenon.compute_translation_vector_given_shoulder(
                    tenon.height_reference_edge, height_shoulder, scale_factor, matrix_world)

                bmesh.ops.translate(bm, vec = translate_vector, space = matrix_world, verts = list(verts_to_translate))

        # Haunched tenon
        if height_properties.centered == False and height_properties.haunched == True:
            if height_properties.haunch_angle == "sloped":
                still_edge_tangent = face_to_be_transformed.shortest_side_tangent
                if height_properties.reverse_shoulder == True:
                    still_edge_tangent.negate()
                self.__set_face_sloped(height_properties.haunch_depth_value,
                                       bm,
                                       matrix_world,
                                       height_shoulder.face,
                                       still_edge_tangent)
            else:
                self.__set_face_depth(height_properties.haunch_depth_value,
                                      bm,
                                      matrix_world,
                                      height_shoulder.face)

        # Set tenon depth
        self.__set_face_depth(tenon_properties.depth_value,
                              bm,
                              matrix_world,
                              tenon.face)


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

    expand_thickness_properties = bpy.props.BoolProperty(name = "Expand", default = True)
    expand_height_properties = bpy.props.BoolProperty(name = "Expand", default = True)


    def __check_face(self, face):
        # If we don't find a selected face, we have problem.  Exit:
        if face == None:
            self.report({'ERROR_INVALID_INPUT'},
                        "You must select a face for the tenon.")
            return False

        # Warn the user if face is not 4 vertices.
        if len(face.verts) > 4 :
            self.report({'ERROR_INVALID_INPUT'},
                        "Selected face is not quad.")
            return False


        if not is_face_planar(face) :
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

        tenonProperties = context.scene.tenonProperties
        thicknessProperties = tenonProperties.thickness_properties
        heightProperties = tenonProperties.height_properties

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if self.expand_thickness_properties == False: 
            row.prop(self, "expand_thickness_properties", icon="TRIA_RIGHT", icon_only=True, text="Width side", emboss=False)
        else:
            row.prop(self, "expand_thickness_properties", icon="TRIA_DOWN", icon_only=True, text="Width side", emboss=False)

            widthSideBox = layout.box()
            widthSideBox.label(text="Thickness type")
            widthSideBox.prop(thicknessProperties, "type", text = "")
            if thicknessProperties.type == "value":
                widthSideBox.prop(thicknessProperties, "value", text = "")
            elif thicknessProperties.type == "percentage":
                widthSideBox.prop(thicknessProperties, "percentage", text = "", slider = True)
            widthSideBox.label(text="Position")
            widthSideBox.prop(thicknessProperties, "centered")
            if thicknessProperties.centered == False:
                widthSideBox.label(text="Thickness shoulder type")
                widthSideBox.prop(thicknessProperties, "shoulder_type", text = "")
                if thicknessProperties.shoulder_type == "value":
                    widthSideBox.prop(thicknessProperties, "shoulder_value", text="")
                elif thicknessProperties.shoulder_type == "percentage":
                    widthSideBox.prop(thicknessProperties, "shoulder_percentage", text = "", slider = True)
                widthSideBox.prop(thicknessProperties, "reverse_shoulder")

        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        if self.expand_height_properties == False: 
            row.prop(self, "expand_height_properties", icon="TRIA_RIGHT", icon_only=True, text="Length side", emboss=False)
        else:
            row.prop(self, "expand_height_properties", icon="TRIA_DOWN", icon_only=True, text="Length side", emboss=False)

            lengthSideBox = layout.box()
            lengthSideBox.label(text="Height type")
            lengthSideBox.prop(heightProperties, "type", text = "")
            if heightProperties.type == "value" :
                lengthSideBox.prop(heightProperties, "value", text = "")
            elif heightProperties.type == "percentage":
                lengthSideBox.prop(heightProperties, "percentage", text = "", slider = True)
            lengthSideBox.label(text="Position")
            lengthSideBox.prop(heightProperties, "centered")
            if heightProperties.centered == False:
                lengthSideBox.label(text="Height shoulder type")
                lengthSideBox.prop(heightProperties, "shoulder_type", text = "")
                if heightProperties.shoulder_type == "value" :
                    lengthSideBox.prop(heightProperties, "shoulder_value", text="")
                elif heightProperties.shoulder_type == "percentage":
                    lengthSideBox.prop(heightProperties, "shoulder_percentage", text = "", slider = True)
                lengthSideBox.prop(heightProperties, "reverse_shoulder")
                lengthSideBox.prop(heightProperties, "haunched")
                if heightProperties.haunched == True:
                    lengthSideBox.label(text = "Haunch depth type")
                    lengthSideBox.prop(heightProperties, "haunch_type", text = "")
                    if heightProperties.haunch_type == "value" :
                        lengthSideBox.prop(heightProperties, "haunch_depth_value", text="")
                    elif heightProperties.haunch_type == "percentage":
                        lengthSideBox.prop(heightProperties, "haunch_depth_percentage", text = "", slider = True)
                    lengthSideBox.label(text = "Haunch angle")
                    lengthSideBox.prop(heightProperties, "haunch_angle", text = "")

        layout.label(text = "Depth")
        layout.prop(tenonProperties, "depth_value", text = "")


    # used to check if the operator can run
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return(ob and ob.type == 'MESH' and context.mode == 'EDIT_MESH')

    def execute(self, context):

        sce = context.scene

        tenon_properties = context.scene.tenonProperties
        thickness_properties = tenon_properties.thickness_properties
        height_properties = tenon_properties.height_properties

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

        # Check if face could be tenonified ...
        if self.__check_face(face) == False:
            return {'CANCELLED'}

        # Split edges to avoid affecting linked faces when subdividing
        edges_to_split = [edge for edge in face.edges]
        ret = bmesh.ops.split_edges(bm, edges=edges_to_split)
        del ret

        # Extract face infos
        face_to_be_transformed = FaceToBeTransformed(face)
        face_to_be_transformed.extract_features(matrix_world)

        # Init default values, look if face has changed too
        if thickness_properties.value == -1.0 or (not nearlyEqual(face_to_be_transformed.shortest_length, self.shortest_length)) :
            thickness_properties.value = face_to_be_transformed.shortest_length / 3.0
            thickness_properties.percentage = 1.0 / 3.0
            thickness_properties.centered = True
        if height_properties.value == -1.0 or (not nearlyEqual(face_to_be_transformed.longest_length, self.longest_length)) :
            height_properties.value = (face_to_be_transformed.longest_length * 2.0) / 3.0
            height_properties.percentage = 2.0 / 3.0
            height_properties.centered = True
        if tenon_properties.depth_value == -1.0 or (not nearlyEqual(face_to_be_transformed.longest_length, self.longest_length)) :
            tenon_properties.depth_value = face_to_be_transformed.shortest_length
            height_properties.haunch_depth_value = tenon_properties.depth_value / 3.0
            height_properties.haunch_depth_percentage = 1.0 / 3.0

        self.shortest_length = face_to_be_transformed.shortest_length    # used to reinit default values when face changes
        self.longest_length = face_to_be_transformed.longest_length

        # If percentage specified, compute length values
        if thickness_properties.type == "percentage":
            thickness_properties.value = face_to_be_transformed.shortest_length * thickness_properties.percentage

        if height_properties.type == "percentage":
            height_properties.value = face_to_be_transformed.longest_length * height_properties.percentage

        # Init values linked to shoulder size
        if thickness_properties.centered == True:
            thickness_properties.shoulder_value = (face_to_be_transformed.shortest_length - thickness_properties.value) / 2.0
            thickness_properties.shoulder_percentage = thickness_properties.shoulder_value / face_to_be_transformed.shortest_length
        if height_properties.centered == True:
            height_properties.shoulder_value = (face_to_be_transformed.longest_length - height_properties.value) / 2.0
            height_properties.shoulder_percentage = height_properties.shoulder_value / face_to_be_transformed.longest_length

        # If shoulder percentage specified, compute length values
        if thickness_properties.shoulder_type == "percentage":
            thickness_properties.shoulder_value = face_to_be_transformed.shortest_length * thickness_properties.shoulder_percentage
            if thickness_properties.shoulder_value + thickness_properties.value > face_to_be_transformed.shortest_length:
                thickness_properties.value = face_to_be_transformed.shortest_length - thickness_properties.shoulder_value
                thickness_properties.percentage = thickness_properties.value / face_to_be_transformed.shortest_length

        if height_properties.shoulder_type == "percentage":
            height_properties.shoulder_value = face_to_be_transformed.longest_length * height_properties.shoulder_percentage
            if height_properties.shoulder_value + height_properties.value > face_to_be_transformed.longest_length:
                height_properties.value = face_to_be_transformed.longest_length - height_properties.shoulder_value
                height_properties.percentage = height_properties.value / face_to_be_transformed.longest_length

        if height_properties.haunch_type == "percentage":
            height_properties.haunch_depth_value = tenon_properties.depth_value * height_properties.haunch_depth_percentage

        # Check input values
        total_length = height_properties.shoulder_value + height_properties.value
        if (not nearlyEqual(total_length, face_to_be_transformed.longest_length)) and (total_length > face_to_be_transformed.longest_length):
            self.report({'ERROR_INVALID_INPUT'},
                        "Size of length size shoulder and tenon height are too long.")
            return {'CANCELLED'}

        total_length = thickness_properties.shoulder_value + thickness_properties.value
        if  (not nearlyEqual(total_length, face_to_be_transformed.shortest_length)) and (total_length > face_to_be_transformed.shortest_length):
            self.report({'ERROR_INVALID_INPUT'},
                        "Size of width size shoulder and tenon thickness are too long.")
            return {'CANCELLED'}

        # Create tenon
        tenon_creator = TenonCreator(face_to_be_transformed)
        tenon_creator.create(bm, matrix_world, tenon_properties)

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

