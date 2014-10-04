import bmesh
import bpy
from mathutils.geometry import (intersect_point_line,
                                distance_point_to_plane,
                                intersect_line_plane)
from math import pi
from sys import float_info
from collections import namedtuple
from enum import IntEnum


ZERO_TOLERANCE = 0.00001


# Used to retrieve faces when geometry has been deleted and faces reordered
class ReferenceGeometry(IntEnum):
    firstShoulder = 1
    secondShoulder = 2
    extruded = 3
    tenonHaunchAdjacentFace = 4
    edgeToRaise = 5
    haunchAdjacentEdge = 6


# Use bmesh layers to retrieve faces
class GeometryRetriever:
    def __init__(self):
        self.bm = None
        self.face_retriever = None
        self.edge_retriever = None

    def create(self, bm):
        self.bm = bm
        self.face_retriever = bm.faces.layers.int.new("face_retriever")
        self.edge_retriever = bm.edges.layers.int.new("edge_retriever")

    def save_face(self, face, reference_geometry):
        face[self.face_retriever] = int(reference_geometry)

    def retrieve_face(self, reference_geometry, remove_ref=True):
        found = None
        for f in self.bm.faces:
            if f[self.face_retriever] == int(reference_geometry):
                found = f
                if remove_ref:
                    f[self.face_retriever] = 0
                break
        return found

    def save_edge(self, edge, reference_geometry):
        edge[self.edge_retriever] = int(reference_geometry)

    def retrieve_edge(self, reference_geometry, remove_ref=True):
        found = None
        for e in self.bm.edges:
            if e[self.edge_retriever] == int(reference_geometry):
                found = e
                if remove_ref:
                    e[self.edge_retriever] = 0
                break
        return found

    def destroy(self):
        self.bm.faces.layers.int.remove(self.face_retriever)
        self.bm.edges.layers.int.remove(self.edge_retriever)


def nearly_equal(a, b, epsilon=ZERO_TOLERANCE):
    abs_a = abs(a)
    abs_b = abs(b)
    diff = abs(a - b)

    if a == b:
        return True
    elif a == 0.0 or b == 0.0 or diff < float_info.min:
        return diff < (epsilon * float_info.min)
    else:
        return diff / (abs_a + abs_b) < epsilon


def same_direction(tangent0, tangent1):
    angle = tangent0.angle(tangent1)

    return nearly_equal(angle, 0.0) or nearly_equal(angle, pi)


def distance_point_edge(pt, edge):
    line_p1 = edge.verts[0].co
    line_p2 = edge.verts[1].co
    ret = intersect_point_line(pt, line_p1, line_p2)
    closest_point_on_line = ret[0]
    distance_vector = closest_point_on_line - pt
    return distance_vector.length


class TenonMortiseBuilderThickness:
    pass


class TenonMortiseBuilderHaunch:
    pass


class TenonMortiseBuilderHeight:
    def __init__(self):
        self.haunch_first_side = TenonMortiseBuilderHaunch()
        self.haunch_second_side = TenonMortiseBuilderHaunch()


class TenonMortiseBuilderProps:
    def __init__(self):
        self.height_properties = TenonMortiseBuilderHeight()
        self.thickness_properties = TenonMortiseBuilderThickness()


# This describes the initial face where the tenon will be created
class FaceToBeTransformed:
    def __init__(self, face):
        self.face = face

        self.median = None
        self.normal = None
        self.longest_side_tangent = None
        self.shortest_side_tangent = None
        self.longest_edges = None
        self.shortest_edges = None
        self.shortest_length = None
        self.longest_length = None

    def extract_features(self, matrix_world):
        face = self.face

        self.median = face.calc_center_median()
        self.normal = face.normal

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

        if length0 > length1:
            self.longest_side_tangent = e0.calc_tangent(l0)
            self.shortest_side_tangent = e1.calc_tangent(l1)
            self.longest_edges = [e0, face.loops[2].edge]
            self.shortest_edges = [e1, face.loops[3].edge]
            self.shortest_length = length1
            self.longest_length = length0
        else:
            self.longest_side_tangent = e1.calc_tangent(l1)
            self.shortest_side_tangent = e0.calc_tangent(l0)
            self.longest_edges = [e1, face.loops[3].edge]
            self.shortest_edges = [e0, face.loops[2].edge]
            self.shortest_length = length0
            self.longest_length = length1

    # Subdivide given edges and return created faces
    @staticmethod
    def __subdivide_edges(bm, edges_to_subdivide):
        ret = bmesh.ops.subdivide_edges(
            bm,
            edges=edges_to_subdivide,
            cuts=2,
            use_grid_fill=True)

        # Get the new faces

        # Can't rely on Faces as certain faces are not tagged when only two
        # edges are subdivided
        # see  source / blender / bmesh / operators / bmo_subdivide.c
        new_edges = [bmesh_type
                     for bmesh_type in ret["geom_inner"]
                     if type(bmesh_type) is bmesh.types.BMEdge]
        del ret
        subdivided_faces = set()
        for new_edge in new_edges:
            for linked_face in new_edge.link_faces:
                subdivided_faces.add(linked_face)
        return subdivided_faces

    # Subdivide face to be transformed to a tenon
    def subdivide_face(self, bm, height_properties, thickness_properties):
        edges_to_subdivide = []

        max_centered_height = bool(height_properties.type == "max" and
                                   height_properties.centered)
        max_centered_thickness = bool(thickness_properties.type == "max" and
                                      thickness_properties.centered)

        if max_centered_height and not max_centered_thickness:
            # if tenon height set to maximum, select shortest side edges
            # to subdivide only in this direction
            for edge in self.shortest_edges:
                edges_to_subdivide.append(edge)

        elif max_centered_thickness and not max_centered_height:
            # if tenon thickness set to maximum, select longest side edges
            # to subdivide only in this direction
            for edge in self.longest_edges:
                edges_to_subdivide.append(edge)

        elif not (max_centered_height and max_centered_thickness):
            edges_to_subdivide = self.face.edges

        return FaceToBeTransformed.__subdivide_edges(bm, edges_to_subdivide)


# This structure keep info about the newly created tenon face
class TenonFace:
    def __init__(self, face):
        self.face = face
        self.thickness_faces = []
        self.height_faces = []
        self.thickness_reference_edge = None
        self.height_reference_edge = None

    # find tenon adjacent faces to be translated or resized given user's values
    # - height_faces[] are the faces which follows the direction of the
    # longest side
    # - thickness_faces[] are the faces which follows the direction of the
    # shortest side
    # - thickness_reference_edge and height_reference_edge are tenon edges used
    # to determine scale factor
    def find_adjacent_faces(self,
                            face_to_be_transformed,
                            height_properties,
                            thickness_properties):
        tenon = self.face

        self.thickness_faces.append(tenon)
        self.height_faces.append(tenon)

        longest_side_tangent = face_to_be_transformed.longest_side_tangent
        shortest_side_tangent = face_to_be_transformed.shortest_side_tangent

        # Find faces to resize to obtain tenon base
        tenon_edges = tenon.edges
        for tenon_edge in tenon_edges:
            connected_faces = tenon_edge.link_faces
            for connected_face in connected_faces:
                if connected_face != tenon:
                    # Found face adjacent to tenon
                    connected_loops = tenon_edge.link_loops
                    for connected_loop in connected_loops:
                        if connected_loop.face == connected_face:
                            # Return the tangent at this edge relative to
                            # a face (pointing inward into the face).
                            tangent = tenon_edge.calc_tangent(connected_loop)

                            if same_direction(tangent,
                                              longest_side_tangent):

                                self.height_faces.append(connected_face)

                                if self.height_reference_edge is None:
                                    self.height_reference_edge = tenon_edge
                            else:
                                self.thickness_faces.append(connected_face)

                                if self.thickness_reference_edge is None:
                                    self.thickness_reference_edge = tenon_edge

        if height_properties.type == "max" and height_properties.centered:
            # get tenon side facing the smallest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge

            tangent0 = e0.calc_tangent(l0)

            if same_direction(tangent0,
                              shortest_side_tangent):
                self.thickness_reference_edge = e0
            else:
                self.thickness_reference_edge = e1

        elif thickness_properties.type == "max" and \
                thickness_properties.centered:
            # get tenon side facing the longest side
            l0 = tenon.loops[0]
            e0 = l0.edge
            l1 = tenon.loops[1]
            e1 = l1.edge

            tangent0 = e0.calc_tangent(l0)

            if same_direction(tangent0, longest_side_tangent):
                self.height_reference_edge = e0
            else:
                self.height_reference_edge = e1

    @staticmethod
    def get_scale_factor(reference_edge, matrix_world, resize_value):
        v0 = reference_edge.verts[0].co
        v1 = reference_edge.verts[1].co

        v0_world = matrix_world * v0
        v1_world = matrix_world * v1

        to_be_resized = (v0_world - v1_world).length

        return resize_value / to_be_resized

    @staticmethod
    def compute_translation_vector_given_shoulder(reference_edge,
                                                  shoulder,
                                                  scale_factor,
                                                  matrix_world):

        v0 = reference_edge.verts[0].co
        v1 = reference_edge.verts[1].co

        v0_world = matrix_world * v0
        v1_world = matrix_world * v1

        length1 = distance_point_edge(v1, shoulder.origin_face_edge)
        length0 = distance_point_edge(v0, shoulder.origin_face_edge)

        if length1 > length0:
            edge_vector = v1_world - v0_world
        else:
            edge_vector = v0_world - v1_world
        final_vector = edge_vector * scale_factor

        return final_vector - edge_vector

    @staticmethod
    def find_verts_to_translate(tenon_faces, shoulder_verts):
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

    # gets the shoulder : it's a face in tenon_adjacent_faces that is not
    # the tenon itself
    def get_from_tenon(self,
                       tenon,
                       tenon_adjacent_faces,
                       reverse_shoulder,
                       origin_face_edges):

        for face in tenon_adjacent_faces:
            if face != tenon.face:
                if reverse_shoulder:
                    if self.face is not None:
                        self.face = face
                        # TODO : take the edge that match shoulder face
                        self.origin_face_edge = origin_face_edges[1]
                        break
                    else:
                        self.face = face
                else:
                    self.face = face
                    # TODO : take the edge that match shoulder face
                    self.origin_face_edge = origin_face_edges[0]
                    break

    def find_verts_to_translate(self, origin_face_tangent, tenon_faces):

        # find faces to scale
        shoulder_face = self.face
        shoulder_faces = [shoulder_face]

        for edge in shoulder_face.edges:
            connected_faces = edge.link_faces

            for connected_face in connected_faces:
                if connected_face != shoulder_face:
                    connected_loops = edge.link_loops

                    for connected_loop in connected_loops:
                        if connected_loop.face == shoulder_face:
                            tangent = edge.calc_tangent(connected_loop)

                            if same_direction(tangent, origin_face_tangent):
                                shoulder_faces.append(connected_face)

                                if self.reference_edge is None:
                                    self.reference_edge = edge

        # when height or thickness set to the max and tenon is centered,
        # this could happen...
        if self.reference_edge is None:
            l0 = shoulder_face.loops[0]
            e0 = l0.edge
            l1 = shoulder_face.loops[1]
            e1 = l1.edge

            tangent0 = e0.calc_tangent(l0)

            if same_direction(tangent0, origin_face_tangent):
                self.reference_edge = e0
            else:
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
        if length1 > length0:
            edge_vector = (matrix_world * pt1) - (matrix_world * pt0)
        else:
            edge_vector = (matrix_world * pt0) - (matrix_world * pt1)
        shoulder_length_to_resize = edge_vector.length
        scale_factor = shoulder_value / shoulder_length_to_resize
        final_vector = edge_vector * scale_factor
        return final_vector - edge_vector


class TenonMortiseBuilder:
    def __init__(self, face_to_be_transformed, builder_properties):
        self.face_to_be_transformed = face_to_be_transformed
        self.builder_properties = builder_properties
        self.geometry_retriever = GeometryRetriever()

    # Extrude and fatten to set face length
    @staticmethod
    def __set_face_depth(depth, bm, matrix_world, face):
        ret = bmesh.ops.extrude_discrete_faces(bm, faces=[face])

        extruded_face = ret['faces'][0]
        del ret

        # apply rotation to the normal
        rot_mat = matrix_world.copy().to_3x3().normalized()
        normal_world = rot_mat * extruded_face.normal
        normal_world = normal_world * depth

        bmesh.ops.translate(bm,
                            vec=normal_world,
                            space=matrix_world,
                            verts=extruded_face.verts)

        return extruded_face

    # Extrude and translate an edge of the face to set it sloped
    def __set_face_sloped(self,
                          depth,
                          bm,
                          matrix_world,
                          face_to_extrude,
                          still_edge_tangent):

        face_normal = face_to_extrude.normal

        # Extrude face
        ret = bmesh.ops.extrude_discrete_faces(bm, faces=[face_to_extrude])
        extruded_face = ret['faces'][0]
        del ret

        # apply rotation to the normal
        rot_mat = matrix_world.copy().to_3x3().normalized()
        normal_world = rot_mat * face_normal
        normal_world = normal_world * depth

        # Delete created face on still edge
        for loop in extruded_face.loops:
            edge = loop.edge
            tangent = edge.calc_tangent(loop)
            angle = tangent.angle(still_edge_tangent)
            if nearly_equal(angle, 0.0):
                still_edge = edge
            elif nearly_equal(angle, pi):
                edge_to_raise = edge

        for face in still_edge.link_faces:
            if face is not extruded_face:
                face_to_remove = face
                break

        # remove only face and bottom edge (because there's no face bellow
        # due tu extrude discrete faces)
        self.geometry_retriever.save_face(extruded_face,
                                          ReferenceGeometry.extruded)
        self.geometry_retriever.save_edge(edge_to_raise,
                                          ReferenceGeometry.edgeToRaise)

        delete_faces = 5
        bmesh.ops.delete(bm, geom=[face_to_remove], context=delete_faces)

        extruded_face = self.geometry_retriever.retrieve_face(
            ReferenceGeometry.extruded, remove_ref=False)

        # collapse remaining edges on the sides
        edges_to_collapse = []
        for loop in extruded_face.loops:
            edge = loop.edge
            tangent = edge.calc_tangent(loop)
            angle = tangent.angle(still_edge_tangent)
            if nearly_equal(angle, 0.0):
                # find edge not in extruded_face
                for vert in edge.verts:
                    link_edges = vert.link_edges
                    for link_edge in link_edges:
                        if not link_edge is edge:
                            has_linked_extruded_face = False
                            link_faces = link_edge.link_faces
                            for f in link_faces:
                                if f is extruded_face:
                                    has_linked_extruded_face = True
                            if not has_linked_extruded_face:
                                edges_to_collapse.append(link_edge)

        for edge in edges_to_collapse:
            verts = edge.verts
            merge_co = verts[0].co
            bmesh.ops.pointmerge(bm, verts=verts, merge_co=merge_co)

        extruded_face = self.geometry_retriever.retrieve_face(
            ReferenceGeometry.extruded)
        edge_to_raise = self.geometry_retriever.retrieve_edge(
            ReferenceGeometry.edgeToRaise)

        # Translate edge up
        bmesh.ops.translate(bm,
                            vec=normal_world,
                            space=matrix_world,
                            verts=edge_to_raise.verts)

        return extruded_face

    # resize centered faces
    @staticmethod
    def __resize_faces(bm, faces, direction, scale_factor):
        verts_to_translate_side_neg = set()
        verts_to_translate_side_pos = set()
        translate_vector_pos = None
        translate_vector_neg = None
        for faceToResize in faces:
            for edge in faceToResize.edges:
                v0 = edge.verts[0]
                v1 = edge.verts[1]
                edge_vector = v1.co - v0.co
                if same_direction(edge_vector, direction):

                    center = (v1.co + v0.co) * 0.5
                    signed_distance = distance_point_to_plane(v0.co, center,
                                                              direction)
                    if signed_distance < 0.0:
                        verts_to_translate_side_neg.add(v0)
                        verts_to_translate_side_pos.add(v1)
                    else:
                        verts_to_translate_side_pos.add(v0)
                        verts_to_translate_side_neg.add(v1)

                    if translate_vector_pos is None:
                        if signed_distance < 0.0:
                            vector_to_translate_neg = v0.co - center
                            vector_to_translate_pos = v1.co - center
                        else:
                            vector_to_translate_neg = v1.co - center
                            vector_to_translate_pos = v0.co - center
                        final_vector_neg = vector_to_translate_neg * \
                            scale_factor
                        final_vector_pos = vector_to_translate_pos * \
                            scale_factor
                        translate_vector_neg = final_vector_neg - \
                            vector_to_translate_neg
                        translate_vector_pos = final_vector_pos - \
                            vector_to_translate_pos

        bmesh.ops.translate(
            bm,
            vec=translate_vector_pos,
            verts=list(verts_to_translate_side_pos))
        bmesh.ops.translate(
            bm,
            vec=translate_vector_neg,
            verts=list(verts_to_translate_side_neg))

    # Find tenon face adjacent to haunch
    def __find__tenon_haunch_adjacent_face(self,
                                           side_tangent,
                                           tenon_top):
        builder_properties = self.builder_properties
        is_mortise = builder_properties.depth_value < 0.0

        adjacent_face = None

        for edge in tenon_top.edges:
            for face in edge.link_faces:
                if face != tenon_top:
                    normal = face.normal.copy()
                    if is_mortise:
                        normal.negate()
                    angle = side_tangent.angle(normal)
                    if nearly_equal(angle, pi):
                        adjacent_face = face
                        break
            if adjacent_face is not None:
                break
        return adjacent_face

    # Find vertices in haunch touching tenon face
    @staticmethod
    def __find_haunch_adjacent_edge(adjacent_face, haunch_top):
        adjacent_edge = None
        for edge in haunch_top.edges:
            # find edge in plane adjacent_face
            median = (edge.verts[0].co + edge.verts[1].co) * 0.5

            dist = distance_point_to_plane(median, adjacent_face.verts[0].co,
                                           adjacent_face.normal)

            if abs(dist) < ZERO_TOLERANCE:
                adjacent_edge = edge
                break
        return adjacent_edge

    @staticmethod
    def __find_tenon_faces_on_the_longest_side(face_to_be_transformed,
                                               tenon_top):
        longest_side_tangent = \
            face_to_be_transformed.longest_side_tangent.copy()
        found = []
        for edge in tenon_top.edges:
            for face in edge.link_faces:
                if face != tenon_top:
                    if same_direction(longest_side_tangent, face.normal):
                        found.append(face)
                        break
        return found

    @staticmethod
    def __find_haunch_faces_on_the_longest_side(face_to_be_transformed,
                                                haunch_top):
        longest_side_tangent = \
            face_to_be_transformed.longest_side_tangent.copy()
        found = []
        for edge in haunch_top.edges:
            for face in edge.link_faces:
                if face != haunch_top:
                    if same_direction(longest_side_tangent, face.normal):
                        found.append(face)
                        break
        return found

    # clean tenon : remove face adjacent to the haunch (visible with mortise)
    def __beautify_haunched_tenon(self,
                                  bm,
                                  face_to_be_transformed,
                                  tenon_top,
                                  haunch_top,
                                  side_tangent):

        # 1. Find tenon face adjacent to haunch
        adjacent_face = self.__find__tenon_haunch_adjacent_face(
            side_tangent, tenon_top)
        geometry_retriever_type = ReferenceGeometry.tenonHaunchAdjacentFace
        self.geometry_retriever.save_face(adjacent_face,
                                          geometry_retriever_type)

        # 2. Find vertices in haunch touching tenon face
        adjacent_edge = TenonMortiseBuilder.__find_haunch_adjacent_edge(
            adjacent_face,
            haunch_top)
        self.geometry_retriever.save_edge(adjacent_edge,
                                          ReferenceGeometry.haunchAdjacentEdge)

        # 3. Split tenon edges at vertices
        connections = []

        for vert in adjacent_edge.verts:

            nearest_edge = None
            best_distance = float_info.max
            for edge in adjacent_face.edges:
                # find nearest edge
                dist = distance_point_edge(vert.co, edge)
                if dist < best_distance:
                    nearest_edge = edge
                    best_distance = dist
            connection = dict()
            connection['haunch_vert'] = vert
            connection['tenon_edge'] = nearest_edge
            connections.append(connection)

        for connection in connections:
            tenon_edge = connection['tenon_edge']
            edge_start = tenon_edge.verts[0]
            edge_end = tenon_edge.verts[1]
            haunch_vert = connection['haunch_vert']
            ret = intersect_point_line(haunch_vert.co, edge_start.co,
                                       edge_end.co)
            dist_in_percentage = ret[1]
            ret = bmesh.utils.edge_split(tenon_edge, edge_start,
                                         dist_in_percentage)
            connection['new_vert'] = ret[1]
            del ret

        # 4. Merge created vertices from split edge with those of haunch top
        # face
        verts_to_merge = []
        for connection in connections:
            new_vert = connection['new_vert']
            verts_to_merge.append(new_vert)

        bmesh.ops.automerge(bm, verts=verts_to_merge, dist=ZERO_TOLERANCE)

        # Geometry has changed from now on so all old references may be wrong
        #  (adjacent_edge, adjacent_face ...)
        adjacent_face = self.geometry_retriever.retrieve_face(
            ReferenceGeometry.tenonHaunchAdjacentFace)
        adjacent_edge = self.geometry_retriever.retrieve_edge(
            ReferenceGeometry.haunchAdjacentEdge)

        # 5. Remove face connecting haunch and tenon
        geom_to_delete = []
        for face in adjacent_edge.link_faces:
            if not face is haunch_top:
                geom_to_delete.append(face)

        delete_only_faces = 3
        bmesh.ops.delete(bm, geom=geom_to_delete, context=delete_only_faces)

        # 6. Remove old tenon face and unneeded edge below haunch
        delete_faces = 5
        bmesh.ops.delete(bm, geom=[adjacent_face], context=delete_faces)

        # 7. Rebuild tenon face using new vertices
        face_vertices = [adjacent_edge.verts[0], adjacent_edge.verts[1]]
        for edge in tenon_top.edges:
            for loop in edge.link_loops:
                if loop.face == tenon_top:
                    tangent = edge.calc_tangent(loop)
                    angle = tangent.angle(side_tangent)
                    if nearly_equal(angle, 0):
                        face_vertices.append(edge.verts[0])
                        face_vertices.append(edge.verts[1])
                        break
            if len(face_vertices) > 2:
                break

        bm.faces.new(face_vertices, tenon_top)

        # 9. Dissolve faces on tenon sides
        faces_to_dissolve = \
            TenonMortiseBuilder.__find_tenon_faces_on_the_longest_side(
                face_to_be_transformed, tenon_top)
        faces_to_dissolve.extend(
            TenonMortiseBuilder.__find_haunch_faces_on_the_longest_side(
                face_to_be_transformed, haunch_top))
        bmesh.ops.dissolve_faces(bm, faces=faces_to_dissolve)

    # Find hole face
    def __find_haunch_external_face(self,
                                    face_to_be_transformed,
                                    haunch_top,
                                    side_tangent):
        hole_face = None
        for edge in haunch_top.edges:
            for face in edge.link_faces:
                if face is not haunch_top:
                        angle = side_tangent.angle(face.normal)
                        if nearly_equal(angle, 0.0):
                            hole_face = face
                            break
            if hole_face is not None:
                break
        return hole_face

    def __make_mortise_haunch_hole_on_side_face(self,
                                                bm,
                                                face_to_be_transformed,
                                                haunch_top,
                                                side_tangent):
        # This is the face to transform to an hole
        hole_face = self.__find_haunch_external_face(face_to_be_transformed, haunch_top, side_tangent)

        # Get top edge
        top_edge_to_dissolve = None
        for edge in hole_face.edges:
            v0 = edge.verts[0]
            v1 = edge.verts[1]
            center = (v1.co + v0.co) * 0.5
            distance = distance_point_to_plane(center, face_to_be_transformed.median,
                                               face_to_be_transformed.normal)
            if abs(distance) < ZERO_TOLERANCE:
                top_edge_to_dissolve = edge
                break


        # keep adjacent face flat projecting bottom edge on it
        linked_faces = top_edge_to_dissolve.link_faces
        if len(linked_faces) == 2:
            adjacent_face = None
            for face in linked_faces:
                if face is not hole_face:
                    adjacent_face = face
                    break

            plane_co = adjacent_face.verts[0].co
            adjacent_normal = adjacent_face.normal

            for loop in haunch_top.loops:
                edge = loop.edge
                tangent = edge.calc_tangent(loop)
                if not same_direction(tangent, side_tangent):
                    v0 = loop.vert
                    v1 = loop.link_loop_next.vert

                    intersection_pt = intersect_line_plane(v0.co, v1.co, plane_co, adjacent_normal)
                    v0_distance = abs(distance_point_to_plane(v0.co, plane_co, adjacent_normal))
                    v1_distance = abs(distance_point_to_plane(v1.co, plane_co, adjacent_normal))
                    if v0_distance < v1_distance:
                        origin_pt = v0
                    else:
                        origin_pt = v1
                    translate_vec = intersection_pt - origin_pt.co

                    bmesh.ops.translate(bm,
                                        verts = [origin_pt],
                                        vec = translate_vec)
            # dissolve top edge
            bmesh.ops.dissolve_edges(bm, edges = [top_edge_to_dissolve])


    def __raise_haunched_tenon_side(self, bm, matrix_world,
                                    face_to_be_transformed, tenon_top,
                                    side_tangent, shoulder, haunch_properties):
        if haunch_properties.angle == "sloped":
            haunch_top = self.__set_face_sloped(
                haunch_properties.depth_value,
                bm,
                matrix_world,
                shoulder.face,
                side_tangent)
        else:
            haunch_top = TenonMortiseBuilder.__set_face_depth(
                haunch_properties.depth_value,
                bm,
                matrix_world,
                shoulder.face)

            if haunch_properties.depth_value < 0.0:
                self.__make_mortise_haunch_hole_on_side_face(bm, face_to_be_transformed, haunch_top, side_tangent)

        self.__beautify_haunched_tenon(bm, face_to_be_transformed, tenon_top,
                                       haunch_top, side_tangent)

    # Raise a haunched tenon
    def __raise_haunched_tenon(self,
                               bm,
                               matrix_world,
                               tenon,
                               face_to_be_transformed,
                               first_shoulder,
                               second_shoulder):
        builder_properties = self.builder_properties

        # save some faces
        self.geometry_retriever.save_face(first_shoulder.face,
                                          ReferenceGeometry.firstShoulder)
        self.geometry_retriever.save_face(second_shoulder.face,
                                          ReferenceGeometry.secondShoulder)

        tenon_top = TenonMortiseBuilder.__set_face_depth(
            builder_properties.depth_value,
            bm,
            matrix_world,
            tenon.face)

        # extrude used by __set_face_depth could reorder faces (destructive op)
        # so retrieve saved faces
        first_shoulder.face = self.geometry_retriever.retrieve_face(
            ReferenceGeometry.firstShoulder)
        second_shoulder.face = self.geometry_retriever.retrieve_face(
            ReferenceGeometry.secondShoulder)

        height_properties = builder_properties.height_properties
        side_tangent = face_to_be_transformed.shortest_side_tangent.copy()

        if height_properties.haunched_first_side:
            haunch_properties = height_properties.haunch_first_side
            self.__raise_haunched_tenon_side(bm, matrix_world,
                                             face_to_be_transformed, tenon_top,
                                             side_tangent, first_shoulder,
                                             haunch_properties)
        if height_properties.haunched_second_side:
            side_tangent.negate()
            haunch_properties = height_properties.haunch_second_side
            self.__raise_haunched_tenon_side(bm, matrix_world,
                                             face_to_be_transformed, tenon_top,
                                             side_tangent, second_shoulder,
                                             haunch_properties)

        bpy.ops.mesh.select_all(action="DESELECT")
        tenon_top.select = True

    # Raise a not haunched tenon
    def __raise_simple_tenon(self, bm, matrix_world, tenon):
        depth = self.builder_properties.depth_value
        extruded_face = TenonMortiseBuilder.__set_face_depth(depth,
                                                             bm,
                                                             matrix_world,
                                                             tenon.face)

        bpy.ops.mesh.select_all(action="DESELECT")
        extruded_face.select = True

    def create(self, bm, matrix_world):

        face_to_be_transformed = self.face_to_be_transformed
        builder_properties = self.builder_properties
        thickness_properties = builder_properties.thickness_properties
        height_properties = builder_properties.height_properties

        # Create layers to retrieve geometry when data are deleted (this will
        # reorder face so face_to_be_transformed is not valid anymore ...)
        for face in bm.faces:
            face.tag = False
        for edge in bm.edges:
            edge.tag = False
        face_to_be_transformed.face.tag = True
        self.geometry_retriever.create(bm)
        tagged_faces = [f for f in bm.faces if f.tag]
        face_to_be_transformed.face = tagged_faces[0]
        face_to_be_transformed.face.tag = False
        face_to_be_transformed.extract_features(matrix_world)

        # Subdivide face
        subdivided_faces = face_to_be_transformed.subdivide_face(
            bm,
            height_properties,
            thickness_properties)

        # Find tenon face (face containing median center)
        if len(subdivided_faces) == 0:
            # when max height centered and max thickness centered
            # (stupid choice but should handle this case too...)
            tenon = TenonFace(face_to_be_transformed.face)

        for f in subdivided_faces:
            if bmesh.geometry.intersect_face_point(
                    f,
                    face_to_be_transformed.median):
                tenon = TenonFace(f)
                break

        # Find faces to be resized
        tenon.find_adjacent_faces(face_to_be_transformed,
                                  height_properties,
                                  thickness_properties)

        # Set tenon shoulder on height side
        if not height_properties.centered:
            first_shoulder = ShoulderFace()
            second_shoulder = ShoulderFace()
            first_shoulder.get_from_tenon(
                tenon,
                tenon.thickness_faces,
                False,
                face_to_be_transformed.shortest_edges)
            second_shoulder.get_from_tenon(
                tenon,
                tenon.thickness_faces,
                True,
                face_to_be_transformed.shortest_edges)

            if height_properties.reverse_shoulder:
                height_shoulder = second_shoulder
            else:
                height_shoulder = first_shoulder

            height_shoulder_verts_to_translate = \
                height_shoulder.find_verts_to_translate(
                    face_to_be_transformed.longest_side_tangent,
                    tenon.height_faces)

            translate_vector = height_shoulder.compute_translation_vector(
                height_properties.shoulder_value,
                matrix_world)

            bmesh.ops.translate(
                bm,
                vec=translate_vector,
                space=matrix_world,
                verts=list(height_shoulder_verts_to_translate))

        # Set tenon shoulder on width side
        if not thickness_properties.centered:
            thickness_shoulder = ShoulderFace()
            thickness_shoulder.get_from_tenon(
                tenon,
                tenon.height_faces,
                thickness_properties.reverse_shoulder,
                face_to_be_transformed.longest_edges)

            thickness_shoulder_verts_to_translate = \
                thickness_shoulder.find_verts_to_translate(
                    face_to_be_transformed.shortest_side_tangent,
                    tenon.thickness_faces)

            translate_vector = thickness_shoulder.compute_translation_vector(
                thickness_properties.shoulder_value,
                matrix_world)

            bmesh.ops.translate(
                bm,
                vec=translate_vector,
                space=matrix_world,
                verts=list(thickness_shoulder_verts_to_translate))

        # Set tenon thickness
        if thickness_properties.type != "max":
            scale_factor = TenonFace.get_scale_factor(
                tenon.thickness_reference_edge,
                matrix_world,
                thickness_properties.value)

            if thickness_properties.centered:
                # centered
                TenonMortiseBuilder.__resize_faces(
                    bm,
                    tenon.thickness_faces,
                    face_to_be_transformed.longest_side_tangent,
                    scale_factor)
            else:
                # shouldered
                verts_to_translate = TenonFace.find_verts_to_translate(
                    tenon.thickness_faces,
                    thickness_shoulder_verts_to_translate)

                translate_vector = \
                    TenonFace.compute_translation_vector_given_shoulder(
                        tenon.thickness_reference_edge,
                        thickness_shoulder,
                        scale_factor,
                        matrix_world)

                bmesh.ops.translate(bm,
                                    vec=translate_vector,
                                    space=matrix_world,
                                    verts=list(verts_to_translate))

        # Set tenon height
        if height_properties.type != "max":
            scale_factor = TenonFace.get_scale_factor(
                tenon.height_reference_edge,
                matrix_world,
                height_properties.value)

            if height_properties.centered:
                # centered
                TenonMortiseBuilder.__resize_faces(
                    bm,
                    tenon.height_faces,
                    face_to_be_transformed.shortest_side_tangent,
                    scale_factor)
            else:
                # shouldered
                verts_to_translate = TenonFace.find_verts_to_translate(
                    tenon.height_faces,
                    height_shoulder_verts_to_translate)

                translate_vector = \
                    TenonFace.compute_translation_vector_given_shoulder(
                        tenon.height_reference_edge,
                        height_shoulder,
                        scale_factor,
                        matrix_world)

                bmesh.ops.translate(bm,
                                    vec=translate_vector,
                                    space=matrix_world,
                                    verts=list(verts_to_translate))

        # Raise tenon
        if not height_properties.centered and (
                height_properties.haunched_first_side or
                height_properties.haunched_second_side):
            self.__raise_haunched_tenon(bm, matrix_world, tenon,
                                        face_to_be_transformed, first_shoulder,
                                        second_shoulder)
        else:
            self.__raise_simple_tenon(bm, matrix_world, tenon)

        self.geometry_retriever.destroy()
