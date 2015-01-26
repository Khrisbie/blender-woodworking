from math import modf
import bpy
import mathutils


class Socket:
    def __init__(self, bpy_socket: bpy.types.NodeSocket):
        self.socket = bpy_socket

    def as_bpy_type(self) -> bpy.types.NodeSocket:
        return self.socket


class Nodes:
    def __init__(self, bpy_node_tree: bpy.types.NodeTree):
        self.node_tree = bpy_node_tree

    def link(self,
             input_socket: Socket,
             output_socket: Socket):

        self.node_tree.links.new(input_socket.as_bpy_type(),
                                 output_socket.as_bpy_type())

    def as_bpy_type(self) -> bpy.types.NodeTree:
        return self.node_tree


class Node:
    pass


class Node:

    def __init__(self, bpy_node: bpy.types.Node):
        self.node = bpy_node

    @staticmethod
    def create(tree: Nodes,
               node_type: str) -> Node:
        node_type_to_class = {
            'NodeFrame': Frame,
            'NodeReroute': Reroute,
            'NodeGroupInput': GroupInput,
            'ShaderNodeGroup': GroupNode,
            'ShaderNodeTexCoord': TextureCoordinate,
            'ShaderNodeObjectInfo': ObjectInfo,
            'ShaderNodeMixRGB': MixRGB,
            'ShaderNodeTexNoise': NoiseTexture,
            'ShaderNodeTexGradient': GradientTexture,
            'ShaderNodeTexMusgrave': MusgraveTexture,
            'ShaderNodeValToRGB': ColorRamp,
            'ShaderNodeRGBCurve': RGBCurve,
            'ShaderNodeMath': Math
        }
        nodes = tree.as_bpy_type().nodes
        bpy_node = nodes.new(node_type)
        class_type = node_type_to_class.get(node_type, Node)

        return class_type(bpy_node)

    def set_name(self, name: str) -> Node:
        self.node.name = name
        return self

    def set_label(self, label: str) -> Node:
        self.node.label = label
        return self

    def set_parent(self, parent: Node) -> Node:
        if type(parent) is Frame:
            parent.set_child(self)
        self.node.parent = parent.as_bpy_type()
        return self

    def get_parent(self) -> bpy.types.Node:
        return self.node.parent

    def set_location(self, location: tuple) -> Node:
        self.node.location = location
        return self

    def get_location(self) -> tuple:
        return self.node.location

    def get_width(self)-> float:
        return self.node.width

    def get_height(self)-> float:
        return self.node.height

    def as_bpy_type(self) -> bpy.types.Node:
        return self.node

    def get_input(self, key: str) -> Socket:
        return Socket(self.node.inputs[key])

    def get_input(self, index: int) -> Socket:
        return Socket(self.node.inputs[index])

    def get_output(self, key: str) -> Socket:
        return Socket(self.node.outputs[key])

    def get_output(self, index: int) -> Socket:
        return Socket(self.node.outputs[index])

    def compute_width(self) -> float:
        return self.get_width()

    def on_the_right_side_of(self, ref_node: Node, delta: float) -> Node:
        ref_x, ref_y = ref_node.get_location()
        computed_width = ref_node.compute_width()
        self.set_location((ref_x + computed_width + delta, ref_y))
        return self

    def compute_buttons_y_space(self) -> float:
        return 0.0

    # When widget is not drawn yet, dimensions are not available
    # Values taken from node_update_basis in node_draw.c
    def compute_height(self) -> float:
        widget_unit = 20
        node_dy = widget_unit
        node_dys = widget_unit // 2
        node_sockdy = 0.08 * widget_unit

        node_bpy = self.as_bpy_type()
        if node_bpy.hide:
            hidden_rad = 0.75 * widget_unit
            totout = totin = 0
            for output in node_bpy.outputs:
                if output.hide:
                    continue
                totout += 1
            for input in node_bpy.inputs:
                if input.hide:
                    continue
                totin += 1
            tot = max(totout, totin)
            if tot > 4:
                hidden_rad += 5.0 * (tot - 4.0)
            dy = node_bpy.location.y + hidden_rad - 0.5 * node_dy
        else:
            dy = node_bpy.location.y
            # header
            dy -= node_dy

            # little bit space in top
            if node_bpy.outputs:
                dy -= node_dys // 2
            # output sockets
            i = 0
            for output in node_bpy.outputs:
                if output.hide:
                    continue
                dy = int(dy - node_dy)
                dy -= node_sockdy
                i += 1
            dy += node_sockdy

            # "buttons" rect
            buttons_y_space = self.compute_buttons_y_space()
            if buttons_y_space > 0.0:
                dy -= node_dys // 2
                dy -= buttons_y_space
                dy -= node_dys // 2

            # input sockets
            for input in node_bpy.inputs:
                if input.hide:
                    continue
                dy = int(dy - node_dy)
                dy -= node_sockdy
            dy += node_sockdy

            # little bit space in end
            has_options_or_preview = node_bpy.show_preview or node_bpy.show_options
            if node_bpy.inputs or not has_options_or_preview:
                dy -= node_dys / 2

        return node_bpy.location.y - dy

    def below(self, ref_node: Node, delta: float) -> Node:
        location = ref_node.get_location()
        computed_height = ref_node.compute_height()
        self.set_location((location.x, location.y - computed_height - delta))
        return self

class Group:
    pass


class Group(Nodes):

    @staticmethod
    def create(name: str) -> Group:
        group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
        return Group(group)

    def set_input(self, input_name: str, input_type: str, input_value) -> Group:
        new_input = self.node_tree.inputs.new(name=input_name, type=input_type)
        new_input.default_value = input_value
        return self

    def set_output(self, output_name: str, output_type: str, output_value) -> Group:
        new_output = self.node_tree.outputs.new(name=output_name, type=output_type)
        new_output.default_value = output_value
        return self

    def get_input(self, input_name: str) -> Socket:
        return Socket(self.node_tree.inputs[input_name])

    def get_output(self, output_name: str) -> Socket:
        return Socket(self.node_tree.outputs[output_name])

    def set_float_input(self, input_name: str, input_value: float) -> Group:
        return self.set_input(input_name, 'NodeSocketFloat', input_value)

    def set_vector_input(self, input_name: str, input_value: mathutils.Vector) -> Group:
        return self.set_input(input_name, 'NodeSocketVector', input_value)

    def set_color_input(self, input_name: str, input_value: list) -> Group:
        return self.set_input(input_name, 'NodeSocketColor', input_value)

    def set_vector_output(self, input_name: str, output_value: mathutils.Vector) -> Group:
        return self.set_output(input_name, 'NodeSocketVector', output_value)

    def set_color_output(self, input_name: str, output_value: list) -> Group:
        return self.set_output(input_name, 'NodeSocketColor', output_value)

class Frame(Node):
    pass


class Frame(Node):
    def __init__(self, bpy_node: bpy.types.Node):
        self.children = []
        Node.__init__(self, bpy_node)

    @staticmethod
    def create(tree: Nodes) -> Frame:
        return Node.create(tree, 'NodeFrame')

    def set_shrink(self, shrink: bool) -> Frame:
        self.node.shrink = shrink
        return self

    def set_child(self, child: Node):
        self.children.append(child)

    def compute_width(self) -> float:
        # from node_draw_frame_prepare in drawnode.c
        widget_unit = 20
        margin = 1.5 * widget_unit

        width = self.node.width

        # get children and compute bounding box
        lowest_x = 99999999999999999.0
        highest_x = -99999999999999999.0
        if len(self.children) > 0:
            for child in self.children:
                child_loc = child.get_location()
                child_x = child_loc.x - margin
                if child_x < lowest_x:
                    lowest_x = child_x
                child_width = child.compute_width()
                child_xmax = child_loc.x + child_width + margin
                if child_xmax > highest_x:
                    highest_x = child_xmax
            width = highest_x - lowest_x

        return width

    def compute_height(self) -> float:
        # from node_draw_frame_prepare in drawnode.c
        widget_unit = 20
        margin = 1.5 * widget_unit

        height = self.node.height

        # get children and compute bounding box
        lowest_y = 99999999999999999.0
        highest_y = -99999999999999999.0
        if len(self.children) > 0:
            for child in self.children:
                child_loc = child.get_location()
                child_y = child_loc.y + margin
                if child_y > highest_y:
                    highest_y = child_y
                child_height = child.compute_height()
                child_ymax = child_loc.y - child_height - margin
                if child_ymax < lowest_y:
                    lowest_y = child_ymax
            height = highest_y - lowest_y

        return height


class Reroute(Node):
    pass


class Reroute(Node):
    @staticmethod
    def create(tree: Nodes) -> Reroute:
        return Node.create(tree, 'NodeReroute')


class GroupNode(Node):
    pass


class GroupInput(Node):
    pass


class GroupInput(Node):
    @staticmethod
    def create(tree: Nodes) -> GroupInput:
        return Node.create(tree, 'NodeGroupInput')


class GroupOutput(Node):
    pass


class GroupOutput(Node):
    @staticmethod
    def create(tree: Nodes) -> GroupOutput:
        return Node.create(tree, 'NodeGroupOutput')


class TextureCoordinate(Node):
    pass


class ObjectInfo(Node):
    pass


class MixRGB(Node):
    pass


class MixRGB(Node):
    @staticmethod
    def create(tree: Nodes) -> MixRGB:
        return Node.create(tree, 'ShaderNodeMixRGB')

    def set_blend_type(self, blend_type: str) -> MixRGB:
        self.node.blend_type = blend_type
        return self

    def set_use_clamp(self, use_clamp: bool) -> MixRGB:
        self.node.use_clamp = use_clamp
        return self

    def set_mix_factor(self, mix_factor: float) -> MixRGB:
        self.node.inputs['Fac'].default_value = mix_factor
        return self

    def get_mix_factor_input(self) -> Socket:
        return self.get_input('Fac')

    def set_first_color(self, color: tuple) -> MixRGB:
        self.node.inputs['Color1'].default_value = color
        return self

    def get_first_color_input(self) -> Socket:
        return self.get_input('Color1')

    def set_second_color(self, color: tuple) -> MixRGB:
        self.node.inputs['Color2'].default_value = color
        return self

    def get_second_color_input(self) -> Socket:
        return self.get_input('Color2')

    def get_color_output(self) -> Socket:
        return self.get_output('Color')

    def compute_buttons_y_space(self) -> float:
        widget_unit = 20

        # mix op
        dy = widget_unit

        # use clamp
        dy += widget_unit

        return dy

class NoiseTexture(Node):
    pass


class NoiseTexture(Node):
    @staticmethod
    def create(tree: Nodes) -> NoiseTexture:
        return Node.create(tree, 'ShaderNodeTexNoise')

    def get_vector_input(self) -> Socket:
        return self.get_input('Vector')

    def set_scale(self, scale: float) -> NoiseTexture:
        self.node.inputs['Scale'].default_value = scale
        return self

    def get_scale_input(self) -> Socket:
        return self.get_input('Scale')

    def set_detail(self, detail: float) -> NoiseTexture:
        self.node.inputs['Detail'].default_value = detail
        return self

    def set_distortion(self, distortion: float) -> NoiseTexture:
        self.node.inputs['Distortion'].default_value = distortion
        return self

    def get_color_output(self) -> Socket:
        return self.get_output('Color')

    def get_mix_factor_output(self) -> Socket:
        return self.get_output('Fac')


class GradientTexture(Node):
    pass


class GradientTexture(Node):
    @staticmethod
    def create(tree: Nodes) -> GradientTexture:
        return Node.create(tree, 'ShaderNodeTexGradient')

    def set_type(self, gradient_type: str) -> GradientTexture:
        self.node.gradient_type = gradient_type
        return self

    def get_vector_input(self) -> Socket:
        return self.get_input('Vector')

    def get_color_output(self) -> Socket:
        return self.get_output('Color')

    def compute_buttons_y_space(self) -> float:
        widget_unit = 20

        # gradient type
        dy = widget_unit

        return dy

class MusgraveTexture(Node):
    pass

class MusgraveTexture(Node):
    @staticmethod
    def create(tree: Nodes) -> MusgraveTexture:
        return Node.create(tree, 'ShaderNodeTexMusgrave')

    def set_type(self, musgrave_type: str) -> MusgraveTexture:
        self.node.musgrave_type = musgrave_type
        return self

    def get_vector_input(self) -> Socket:
        return self.get_input('Vector')

    def get_color_output(self) -> Socket:
        return self.get_output('Color')

    def set_scale(self, scale: float) -> MusgraveTexture:
        self.node.inputs['Scale'].default_value = scale
        return self

    def get_scale_input(self) -> Socket:
        return self.get_input('Scale')

    def set_detail(self, detail: float) -> MusgraveTexture:
        self.node.inputs['Detail'].default_value = detail
        return self

    def set_dimension(self, dimension: float) -> MusgraveTexture:
        self.node.inputs['Dimension'].default_value = dimension
        return self

    def set_lacunarity(self, lacunarity: float) -> MusgraveTexture:
        self.node.inputs['Lacunarity'].default_value = lacunarity
        return self

    def set_offset(self, offset: float) -> MusgraveTexture:
        self.node.inputs['Offset'].default_value = offset
        return self

    def set_gain(self, gain: float) -> MusgraveTexture:
        self.node.inputs['Gain'].default_value = gain
        return self

    def get_mix_factor_output(self) -> Socket:
        return self.get_output('Fac')

    def compute_buttons_y_space(self) -> float:
        widget_unit = 20

        # musgrave type
        dy = widget_unit

        return dy


class ColorRamp(Node):
    pass


class ColorRamp(Node):

    def __init__(self, bpy_node: bpy.types.Node):
        self.stop_index = 0
        Node.__init__(self, bpy_node)

    @staticmethod
    def create(tree: Nodes) -> ColorRamp:
        return Node.create(tree, 'ShaderNodeValToRGB')

    def set_interpolation(self, interpolation: str) -> ColorRamp:
        self.node.color_ramp.interpolation = interpolation
        return self

    def set_mix_factor(self, mix_factor: float) -> ColorRamp:
        self.node.inputs['Fac'].default_value = mix_factor
        return self

    def get_mix_factor_input(self) -> Socket:
        return self.get_input('Fac')

    def add_stop(self, position: float, color: tuple) -> ColorRamp:
        elements = self.node.color_ramp.elements
        if self.stop_index == 0:
            elements.remove(elements[0])
            element = elements[0]
            element.position = position
        else:
            element = elements.new(position)
        element.color = color
        self.stop_index += 1
        return self

    def get_color_output(self) -> Socket:
        return self.get_output('Color')

    def compute_width(self):
        widget_unit = 20
        templateColorRamp_width = 10.0 * widget_unit
        node_width = self.get_width()
        if templateColorRamp_width > node_width:
            node_width = templateColorRamp_width
        return node_width

    def compute_buttons_y_space(self) -> float:
        # see uiTemplateColorRamp interface_templates.c
        widget_unit = 20
        template_space = 5

        dy = template_space

        # add/delete/flip/interpolation buttons row
        dy += widget_unit
        dy += 2  # value in colorband_buttons_large

        # colorband
        dy += widget_unit

        # position / color
        dy += 65  # value in colorband_buttons_large

        return dy


class RGBCurve(Node):
    pass


class RGBCurve(Node):
    def __init__(self, bpy_node: bpy.types.Node):
        self.control_point_index = 0
        Node.__init__(self, bpy_node)

    @staticmethod
    def create(tree: Nodes) -> RGBCurve:
        return Node.create(tree, 'ShaderNodeRGBCurve')

    def set_mix_factor(self, mix_factor: float) -> RGBCurve:
        self.node.inputs['Fac'].default_value = mix_factor
        return self

    def set_color(self, color: tuple) -> RGBCurve:
        self.node.inputs['Color'].default_value = color
        return self

    def get_color_input(self) -> Socket:
        return self.get_input('Color')

    def get_color_output(self) -> Socket:
        return self.get_output('Color')

    def add_control_point(self,
                          location: tuple,
                          handle_type: str='AUTO') -> RGBCurve:
        curve = self.node.mapping.curves[3]
        if self.control_point_index > 1:
            point = curve.points.new(0.0, 0.0)
        else:
            point = curve.points[self.control_point_index]
        point.location = location
        point.handle_type = handle_type

        self.control_point_index += 1
        return self

    def compute_buttons_y_space(self) -> float:
        # see node_buts_curvecol in drawnode.c and and curvemap_buttons_layout
        # in interface_templates.c, and templatespace in interface_layout.c ...

        # ui_litem_layout_root in interface_layout.c => column layout set by
        # default with space set to templatespace from uiBlockLayout
        widget_unit = 20
        template_space = 5
        dy = 0.0

        # buttons row
        button_height = widget_unit
        dy += button_height
        dy += template_space

        # curve
        curve_height = 8.0 * widget_unit
        dy += curve_height
        dy += template_space

        # x/y sliders
        sliders_height = widget_unit
        dy += sliders_height
        dy += template_space

        return dy


class Math(Node):
    pass


class Math(Node):
    @staticmethod
    def create(tree: Nodes) -> Math:
        return Node.create(tree, 'ShaderNodeMath')

    def set_operation(self, operation: str) -> Math:
        self.node.operation = operation
        return self

    def set_use_clamp(self, use_clamp: bool) -> Math:
        self.node.use_clamp = use_clamp
        return self

    def set_first_value(self, value: float) -> Math:
        self.node.inputs[0].default_value = value
        return self

    def set_second_value(self, value: float) -> Math:
        self.node.inputs[1].default_value = value
        return self

    def get_first_value_input(self) -> Socket:
        return self.get_input(0)

    def get_second_value_input(self) -> Socket:
        return self.get_input(1)

    def get_value_output(self) -> Socket:
        return self.get_output('Value')

    def compute_buttons_y_space(self) -> float:
        # see node_buts_math in draw_node.c
        widget_unit = 20
        # block layout space
        template_space = 5

        # operation
        dy = widget_unit
        dy += template_space

        # use clamp
        dy += widget_unit
        dy += template_space

        return dy


class WoodPatternBartek:

    def build(self):
        wood_pattern = Group.create("Wood Grain Base Bartek")
        wood_pattern.\
            set_vector_input("Texture coordinates",
                             mathutils.Vector((0.0, 0.0, 0.0))).\
            set_float_input("Tree bend radius", 0.5).\
            set_float_input("Tree bend diversity", 0.2).\
            set_float_input("Additional bend radius", 0.09).\
            set_float_input("Additional bend diversity", 3.0).\
            set_float_input("Growth rings amount", 100.0).\
            set_float_input("Growth rings distort", 0.650).\
            set_float_input("Growth rings distort 2", 0.04).\
            set_color_input("Length axis", [0.0, 1.0, 1.0, 1.0])
        wood_pattern.\
            set_color_output("Grain pattern", [0.0, 0.0, 0.0, 0.0]).\
            set_vector_output("Coordinates", mathutils.Vector((0.0, 0.0, 0.0)))

        group_input = GroupInput.\
            create(wood_pattern).\
            set_location((0.0, 0.0))

        extended_coords = MixRGB.\
            create(wood_pattern).\
            set_label("Extend length axis to infinity").\
            on_the_right_side_of(group_input, 100.0).\
            set_blend_type('MULTIPLY').\
            set_mix_factor(1.0)

        wood_pattern.link(group_input.get_output("Texture coordinates"),
                          extended_coords.get_first_color_input())
        wood_pattern.link(group_input.get_output("Length axis"),
                          extended_coords.get_second_color_input())
        frame, distorted_coords = self.add_distortion(wood_pattern,
                                                      group_input,
                                                      extended_coords)
        reroute = Reroute.\
            create(wood_pattern).\
            below(frame, 50.0)

        frame, textures_color = self.get_textures_color(wood_pattern,
                                                        group_input,
                                                        distorted_coords,
                                                        frame)
        frame, rings_pattern = self.get_rings_color(wood_pattern,
                                             group_input,
                                             textures_color,
                                             frame)

        group_output = GroupOutput.\
            create(wood_pattern).\
            on_the_right_side_of(frame, 100.0)

        wood_pattern.link(rings_pattern, group_output.get_input("Grain pattern"))
        wood_pattern.link(distorted_coords, group_output.get_input("Coordinates"))

    @staticmethod
    def add_distortion(wood_pattern: Group,
                       group_input: Node,
                       tex_coordinates: MixRGB) -> Socket:
        frame = Frame.\
            create(wood_pattern).\
            on_the_right_side_of(tex_coordinates, 50.0).\
            set_label("Distortion").\
            set_shrink(True)

        distort_tex = NoiseTexture.\
            create(wood_pattern).\
            set_parent(frame).\
            set_location((50.0, 0.0)).\
            set_detail(2.0).\
            set_distortion(0.0)
        wood_pattern.link(group_input.get_output("Texture coordinates"),
                          distort_tex.get_vector_input())
        wood_pattern.link(group_input.get_output("Tree bend diversity"),
                          distort_tex.get_scale_input())

        small_distort_tex = NoiseTexture.\
            create(wood_pattern).\
            set_parent(frame).\
            below(distort_tex, 50.0).\
            set_detail(2.0).\
            set_distortion(0.0)
        wood_pattern.link(group_input.get_output("Texture coordinates"),
                          small_distort_tex.get_vector_input())
        wood_pattern.link(group_input.get_output("Additional bend diversity"),
                          small_distort_tex.get_scale_input())

        reset_distort_direction = MixRGB.\
            create(wood_pattern).\
            set_label("Reset direction").\
            set_parent(frame).\
            on_the_right_side_of(distort_tex, 50.0).\
            set_blend_type('SUBTRACT').\
            set_mix_factor(1.0).\
            set_second_color((0.5, 0.5, 0.5, 1.0))
        wood_pattern.link(distort_tex.get_color_output(),
                          reset_distort_direction.get_first_color_input())

        reset_small_distort_direction = MixRGB.\
            create(wood_pattern).\
            set_label("Reset direction").\
            set_parent(frame).\
            on_the_right_side_of(small_distort_tex, 50.0).\
            set_blend_type('SUBTRACT').\
            set_mix_factor(1.0).\
            set_second_color((0.5, 0.5, 0.5, 1.0))
        wood_pattern.link(small_distort_tex.get_color_output(),
                          reset_small_distort_direction.get_first_color_input())

        add_distortion = MixRGB.\
            create(wood_pattern).\
            set_label("Add distortion").\
            set_parent(frame).\
            on_the_right_side_of(reset_distort_direction, 50.0).\
            set_blend_type('ADD')
        wood_pattern.link(group_input.get_output("Tree bend radius"),
                          add_distortion.get_mix_factor_input())
        wood_pattern.link(tex_coordinates.get_color_output(),
                          add_distortion.get_first_color_input())
        wood_pattern.link(reset_distort_direction.get_color_output(),
                          add_distortion.get_second_color_input())

        add_small_distortion = MixRGB.\
            create(wood_pattern).\
            set_label("Add smaller distortion").\
            set_parent(frame).\
            on_the_right_side_of(reset_small_distort_direction, 50.0).\
            set_blend_type('ADD')
        wood_pattern.link(group_input.get_output("Additional bend radius"),
                          add_small_distortion.get_mix_factor_input())
        wood_pattern.link(add_distortion.get_color_output(),
                          add_small_distortion.get_first_color_input())
        wood_pattern.link(reset_small_distort_direction.get_color_output(),
                          add_small_distortion.get_second_color_input())

        return frame, add_small_distortion.get_color_output()

    @staticmethod
    def get_textures_color(wood_pattern: Group,
                           group_input: Node,
                           tex_coordinates: Socket,
                           previous_positional_node: Node) -> Socket:
        frame = Frame.\
            create(wood_pattern).\
            on_the_right_side_of(previous_positional_node, 50.0).\
            set_label("Textures").\
            set_shrink(True)

        gradient = GradientTexture.\
            create(wood_pattern).\
            set_parent(frame).\
            set_location((50.0, 0.0)).\
            set_type('SPHERICAL')
        wood_pattern.link(tex_coordinates, gradient.get_vector_input())

        first_noise_tex = NoiseTexture.\
            create(wood_pattern).\
            set_parent(frame).\
            below(gradient, 50.0).\
            set_detail(16.0).\
            set_distortion(9.5)
        wood_pattern.link(tex_coordinates, first_noise_tex.get_vector_input())

        second_noise_tex = NoiseTexture.\
            create(wood_pattern).\
            set_parent(frame).\
            below(first_noise_tex, 50.0).\
            set_detail(18.0).\
            set_distortion(8.0)
        wood_pattern.link(tex_coordinates, second_noise_tex.get_vector_input())

        ramp_second_noise = ColorRamp.\
            create(wood_pattern).\
            set_parent(frame).\
            on_the_right_side_of(second_noise_tex, 50.0).\
            add_stop(0.456, (0.0, 0.0, 0.0, 1.0)).\
            add_stop(1.0, (1.0, 1.0, 1.0, 1.0))
        wood_pattern.link(second_noise_tex.get_color_output(),
                          ramp_second_noise.get_mix_factor_input())

        overlay_first_noise = MixRGB.\
            create(wood_pattern).\
            set_parent(frame).\
            on_the_right_side_of(first_noise_tex, 50.0).\
            set_blend_type('OVERLAY')
        wood_pattern.link(group_input.get_output("Growth rings distort"),
                          overlay_first_noise.get_mix_factor_input())
        wood_pattern.link(gradient.get_color_output(),
                          overlay_first_noise.get_first_color_input())
        wood_pattern.link(first_noise_tex.get_color_output(),
                          overlay_first_noise.get_second_color_input())

        overlay_second_noise = MixRGB.\
            create(wood_pattern).\
            set_parent(frame).\
            on_the_right_side_of(ramp_second_noise, 50.0).\
            set_blend_type('OVERLAY')
        wood_pattern.link(group_input.get_output("Growth rings distort 2"),
                          overlay_second_noise.get_mix_factor_input())
        wood_pattern.link(overlay_first_noise.get_color_output(),
                          overlay_second_noise.get_first_color_input())
        wood_pattern.link(ramp_second_noise.get_color_output(),
                          overlay_second_noise.get_second_color_input())

        return frame, overlay_second_noise.get_color_output()

    @staticmethod
    def get_rings_color(wood_pattern: Group,
                        group_input: Node,
                        textures_color: Socket,
                        previous_positional_node: Node) -> Socket:
        frame = Frame.\
            create(wood_pattern).\
            on_the_right_side_of(previous_positional_node, 50.0).\
            set_label("Rings").\
            set_shrink(True)

        density_control = RGBCurve.\
            create(wood_pattern).\
            set_label("Rings density").\
            set_parent(frame).\
            set_location((50.0, 0.0)).\
            add_control_point((0.0, 0.0)).\
            add_control_point((0.309, 0.462)).\
            add_control_point((0.886, 0.831)).\
            add_control_point((1.0, 1.0))
        wood_pattern.link(textures_color,
                          density_control.get_color_input())

        rings_count = Math.\
            create(wood_pattern).\
            set_label("Rings count").\
            set_parent(frame).\
            below(density_control, 50.0).\
            set_operation('DIVIDE').\
            set_first_value(1.0)
        wood_pattern.link(group_input.get_output("Growth rings amount"),
                          rings_count.get_second_value_input())

        make_rings = Math.\
            create(wood_pattern).\
            set_label("Make rings").\
            set_parent(frame).\
            on_the_right_side_of(density_control, 50.0).\
            set_operation('MODULO')
        wood_pattern.link(density_control.get_color_output(),
                          make_rings.get_first_value_input())
        wood_pattern.link(rings_count.get_value_output(),
                          make_rings.get_second_value_input())

        restore_brightness = Math.\
            create(wood_pattern).\
            set_label("Restore brightness").\
            set_parent(frame).\
            on_the_right_side_of(make_rings, 50.0).\
            set_operation('DIVIDE')
        wood_pattern.link(make_rings.get_value_output(),
                          restore_brightness.get_first_value_input())
        wood_pattern.link(rings_count.get_value_output(),
                          restore_brightness.get_second_value_input())

        make_softest_transition = RGBCurve.\
            create(wood_pattern).\
            set_label("Softest transition").\
            set_parent(frame).\
            on_the_right_side_of(restore_brightness, 50.0).\
            add_control_point((0.0, 0.0)).\
            add_control_point((0.923, 1.0), 'VECTOR').\
            add_control_point((1.0, 0.0))
        wood_pattern.link(restore_brightness.get_value_output(),
                          make_softest_transition.get_color_input())
        return frame, make_softest_transition.get_color_output()


# support fibres are "dark background"
class SupportFibresCekhunen:
    def build(self):
        support_fibres = Group.create("Support fibres")

        support_fibres.\
            set_vector_input("Texture coordinates",
                             mathutils.Vector((0.0, 0.0, 0.0))).\
            set_color_input("Color1", [0.413, 0.165, 0.038, 1.0]).\
            set_color_input("Color2", [0.546, 0.216, 0.048, 1.0]).\
            set_color_input("Length scale", [0.05, 1.0, 1.0, 1.0]).\
            set_color_input("Depth scale", [1.0, 1.0, 0.5, 1.0]).\
            set_float_input("Fractal texture scale", 2000.0)
        support_fibres.\
            set_color_output("Color", [0.0, 0.0, 0.0, 0.0])

        group_input = GroupInput.\
            create(support_fibres).\
            set_location((0.0, 0.0))

        scale_length = MixRGB.\
            create(support_fibres).\
            set_label("Scale length").\
            on_the_right_side_of(group_input, 50.0).\
            set_blend_type('MULTIPLY').\
            set_mix_factor(1.0)
        support_fibres.link(group_input.get_output("Texture coordinates"),
                            scale_length.get_first_color_input())
        support_fibres.link(group_input.get_output("Length scale"),
                            scale_length.get_second_color_input())

        scale_depth = MixRGB.\
            create(support_fibres).\
            set_label("Scale depth").\
            on_the_right_side_of(scale_length, 50.0).\
            set_blend_type('MULTIPLY').\
            set_mix_factor(1.0)
        support_fibres.link(scale_length.get_color_output(),
                            scale_depth.get_first_color_input())
        support_fibres.link(group_input.get_output("Depth scale"),
                            scale_depth.get_second_color_input())

        musgrave = MusgraveTexture.\
            create(support_fibres).\
            on_the_right_side_of(scale_depth, 50.0).\
            set_type('FBM').\
            set_detail(3.0).\
            set_dimension(2.0).\
            set_lacunarity(1.0).\
            set_offset(0.0).\
            set_gain(1.0)
        support_fibres.link(scale_depth.get_color_output(),
                            musgrave.get_vector_input())
        support_fibres.link(group_input.get_output("Fractal texture scale"),
                            musgrave.get_scale_input())

        mix = MixRGB.\
            create(support_fibres).\
            on_the_right_side_of(musgrave, 50.0).\
            set_blend_type('MIX')
        support_fibres.link(musgrave.get_mix_factor_output(),
                            mix.get_mix_factor_input())
        support_fibres.link(group_input.get_output("Color1"),
                            mix.get_first_color_input())
        support_fibres.link(group_input.get_output("Color2"),
                            mix.get_second_color_input())

        group_output = GroupOutput.\
            create(support_fibres).\
            on_the_right_side_of(mix, 50.0)

        support_fibres.link(mix.get_color_output(),
                            group_output.get_input("Color"))

class AxialParenchimaCekhunen:

    def build(self):
        axial_parenchima = Group.create("Axial Parenchima")
        axial_parenchima.\
            set_vector_input("Texture coordinates",
                             mathutils.Vector((0.0, 0.0, 0.0))).\
            set_color_input("Color1", [0.694, 0.275, 0.061, 1.0]).\
            set_color_input("Color2", [0.831, 0.546, 0.238, 1.0]).\
            set_color_input("Length scale", [0.1, 1.0, 1.0, 1.0]).\
            set_float_input("Noise scale", 200.0)
        axial_parenchima.\
            set_color_output("Color", [0.0, 0.0, 0.0, 0.0])

        group_input = GroupInput.\
            create(axial_parenchima).\
            set_location((0.0, 0.0))

        scale = MixRGB.\
            create(axial_parenchima).\
            set_label("Scale length").\
            on_the_right_side_of(group_input, 50.0).\
            set_blend_type('MULTIPLY').\
            set_mix_factor(1.0)
        axial_parenchima.link(group_input.get_output("Texture coordinates"),
                              scale.get_first_color_input())
        axial_parenchima.link(group_input.get_output("Length scale"),
                              scale.get_second_color_input())

        noise = NoiseTexture.\
            create(axial_parenchima).\
            on_the_right_side_of(scale, 50.0).\
            set_detail(5.0).\
            set_distortion(5.0)
        axial_parenchima.link(scale.get_color_output(),
                              noise.get_vector_input())
        axial_parenchima.link(group_input.get_output("Noise scale"),
                              noise.get_scale_input())

        mix = MixRGB.\
            create(axial_parenchima).\
            on_the_right_side_of(noise, 50.0).\
            set_blend_type('MIX')
        axial_parenchima.link(noise.get_mix_factor_output(),
                              mix.get_mix_factor_input())
        axial_parenchima.link(group_input.get_output("Color1"),
                              mix.get_first_color_input())
        axial_parenchima.link(group_input.get_output("Color2"),
                              mix.get_second_color_input())

        group_output = GroupOutput.\
            create(axial_parenchima).\
            on_the_right_side_of(mix, 50.0)

        axial_parenchima.link(mix.get_color_output(),
                              group_output.get_input("Color"))


def test():
    mat = bpy.data.materials.new("WoodMaterial")
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nodes = Nodes(mat.node_tree)
    #wood_pattern = WoodPatternBartek()
    #wood_pattern.build()
    #axial_parenchima = AxialParenchimaCekhunen()
    #axial_parenchima.build()
    support_fibres = SupportFibresCekhunen()
    support_fibres.build()
test()