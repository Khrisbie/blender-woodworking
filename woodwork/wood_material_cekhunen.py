import bpy

# dans la doc regarder à ShaderNode dans bpy.types
# print("active node", D.materials["Wood Complex"].node_tree.nodes.active)
# print("active node location", D.materials["Wood Complex"].node_tree.nodes.active.location)
# print("keys", D.materials["Wood Complex"].node_tree.nodes.active.inputs.keys())
class Nodes:
    def __init__(self, node_tree: bpy.types.NodeTree):
        self.node_tree = node_tree

    def create_node(self,
                    node_type: str,
                    name: str,
                    location,
                    parent: bpy.types.Node=None,
                    label: str="") -> bpy.types.Node:
        nodes = self.node_tree.nodes
        node = nodes.new(node_type)
        node.name = name

        node.label = label
        if parent:
            node.parent = parent
        # apply location after parenting to put nodes in frames coordinates
        node.location = location
        return node

    def link_nodes(self,
                   input_node: bpy.types.Node,
                   input_socket_key: str,
                   output_node: bpy.types.Node,
                   output_socket_key: str):

        input_socket = input_node.outputs[input_socket_key]
        output_socket = output_node.inputs[output_socket_key]
        self.node_tree.links.new(input_socket, output_socket) 

    def link_nodes(self,
                   input_node: bpy.types.Node,
                   input_socket_index: int,
                   output_node: bpy.types.Node,
                   output_socket_index: int):
        input_socket = input_node.outputs[input_socket_index]
        output_socket = output_node.inputs[output_socket_index]
        self.node_tree.links.new(input_socket, output_socket)

# credits goes to 'cekhunen' for this material
# http://blenderartists.org/forum/showthread.php?296800-Free-Procedural-wood-with-Cycles-Blend-file-attached
class WoodMaterialCekhunen:
    def __init__(self, nodes: Nodes):
        self.nodes = nodes

    def wood_pattern(self, object_texture_coordinate: bpy.types.ShaderNodeTexCoord):
        frame = self.nodes.create_node('NodeFrame',
                                       'Wood Pattern',
                                       (-556.0108032226562, -67.50959777832031),
                                       label="Wood Pattern")
        frame.shrink = True

        node_mapping = self.nodes.create_node('ShaderNodeMapping',
                                              'Mapping',
                                              (-261.8198, -21.6075),
                                              frame)
        node_mapping.vector_type = 'POINT'
        node_mapping.translation = (-0.39, 0.05, 2.0)
        node_mapping.rotation = (0.0, 0.0, 0.0)
        node_mapping.scale = (2.0, 0.21, 1.0)
        self.nodes.link_nodes(object_texture_coordinate, "Object",
                              node_mapping, "Vector")

        node_wave = self.nodes.create_node('ShaderNodeTexWave',
                                           'Wave Texture',
                                           (151.5857, -5.1366),
                                           frame)
        node_wave.wave_type = 'RINGS'
        node_wave.inputs['Scale'].default_value = 10.0
        node_wave.inputs['Distortion'].default_value = 8.0
        node_wave.inputs['Detail'].default_value = 0.0
        node_wave.inputs['Detail Scale'].default_value = 0.5
        self.nodes.link_nodes(node_mapping, "Vector",
                              node_wave, "Vector")

        node_color_ramp = self.nodes.create_node('ShaderNodeValToRGB',
                                                 'ColorRamp',
                                                 (346.0445, 142.0305),
                                                 frame)
        color_ramp = node_color_ramp.color_ramp
        color_ramp.interpolation = "LINEAR"
        color_ramp_1 = color_ramp.elements[1]
        color_ramp_1.position = 0.282
        color_ramp_1.color = (1.0, 1.0, 1.0, 1.0)
        self.nodes.link_nodes(node_wave, "Color",
                              node_color_ramp, "Fac")

        node_mix = self.nodes.create_node('ShaderNodeMixRGB',
                                          'Mix',
                                          (680.0310, 138.8224),
                                          frame)
        node_mix.blend_type = "MIX"
        node_mix.inputs['Color1'].default_value = (0.332, 0.063, 0.019, 1.0)
        node_mix.inputs['Color2'].default_value = (0.503, 0.109, 0.023, 1.0)
        self.nodes.link_nodes(node_color_ramp, 'Color',
                              node_mix, 'Fac')

        return node_mapping, node_wave, node_color_ramp, node_mix

    def pores_wood_rings(self,
                         node_pores: bpy.types.NodeFrame,
                         node_pores_rings_mapping: bpy.types.ShaderNodeMapping,
                         node_wood_pattern_wave: bpy.types.ShaderNodeTexWave,
                         node_wood_pattern_mix: bpy.types.ShaderNodeMixRGB):
        frame = self.nodes.create_node('NodeFrame',
                                       'Wood Rings',
                                       (342.2466, -234.3675),
                                       node_pores,
                                       label="Wood Rings")
        frame.shrink = True

        node_noise = self.nodes.create_node('ShaderNodeTexNoise',
                                            'Noise Texture',
                                            (15.16571044921875, -37.4923095703125),
                                            frame)
        node_noise.inputs['Scale'].default_value = 300.0
        node_noise.inputs['Detail'].default_value = 0.0
        node_noise.inputs['Distortion'].default_value = 0.0
        self.nodes.link_nodes(node_pores_rings_mapping, "Vector",
                              node_noise, "Vector")

        node_mix = self.nodes.create_node('ShaderNodeMixRGB',
                                          'Mix',
                                          (445.2010192871094, -28.737884521484375),
                                          frame)
        node_mix.blend_type = "MIX"
        node_mix.inputs['Color1'].default_value = (0.040, 0.006, 0.002, 1.0)
        self.nodes.link_nodes(node_wood_pattern_mix, 'Color',
                              node_mix, 'Color2')
        self.nodes.link_nodes(node_noise, 'Color',
                              node_mix, 'Fac')

        node_color_ramp = self.nodes.create_node('ShaderNodeValToRGB',
                                                 'ColorRamp',
                                                 (226.20462036132812, -229.03240966796875),
                                                 frame)
        color_ramp = node_color_ramp.color_ramp
        color_ramp.interpolation = "LINEAR"
        color_ramp_1 = color_ramp.elements[1]
        color_ramp_1.color = (1.0, 1.0, 1.0, 1.0)
        self.nodes.link_nodes(node_wood_pattern_wave, "Color",
                              node_color_ramp, "Fac")

        node_mix_rings_pattern = self.nodes.create_node('ShaderNodeMixRGB',
                                                        'Mix',
                                                        (787.9771728515625, -225.37820434570312),
                                                        frame)
        node_mix_rings_pattern.blend_type = "MIX"
        self.nodes.link_nodes(node_color_ramp, 'Alpha',
                              node_mix_rings_pattern, 'Fac')
        self.nodes.link_nodes(node_mix, 'Color',
                              node_mix_rings_pattern, 'Color1')
        self.nodes.link_nodes(node_wood_pattern_mix, 'Color',
                              node_mix_rings_pattern, 'Color2')

        return node_noise, node_color_ramp, node_mix_rings_pattern

    def pores_dark(self,
                   node_pores: bpy.types.NodeFrame,
                   node_pores_dark_mapping: bpy.types.ShaderNodeMapping):
        frame = self.nodes.create_node('NodeFrame',
                                       'Dark',
                                       (717.8733, 44.3247),
                                       node_pores,
                                       label="Dark")
        frame.shrink = True

        node_noise = self.nodes.create_node('ShaderNodeTexNoise',
                                            'Noise Texture',
                                            (-29.734375, -10.9783935546875),
                                            frame)
        node_noise.inputs['Scale'].default_value = 400.0
        node_noise.inputs['Detail'].default_value = 0.0
        node_noise.inputs['Distortion'].default_value = 0.0
        self.nodes.link_nodes(node_pores_dark_mapping, "Vector",
                              node_noise, "Vector")

        node_color_ramp = self.nodes.create_node('ShaderNodeValToRGB',
                                                 'ColorRamp',
                                                 (202.0432891845703, 8.6156005859375),
                                                 frame)
        color_ramp = node_color_ramp.color_ramp
        color_ramp.interpolation = "LINEAR"
        color_ramp_0 = color_ramp.elements[0]
        color_ramp_0.position = 0.355
        color_ramp_0.color = (1.0, 1.0, 1.0, 0.0)
        color_ramp_1 = color_ramp.elements[1]
        color_ramp_1.position = 0.464
        color_ramp_1.color = (0.0, 0.0, 0.0, 1.0)
        self.nodes.link_nodes(node_noise, "Color",
                              node_color_ramp, "Fac")

        return node_color_ramp

    def pores(self,
              object_texture_coordinate: bpy.types.ShaderNodeTexCoord,
              node_wood_pattern_wave: bpy.types.ShaderNodeTexWave,
              node_wood_pattern_mix: bpy.types.ShaderNodeMixRGB):
        frame = self.nodes.create_node('NodeFrame',
                                       'Pores',
                                       (-745.2870, 847.4890),
                                       label="Pores")
        frame.shrink = True

        dark_node_mapping = self.nodes.create_node('ShaderNodeMapping',
                                                   'Mapping',
                                                   (-63.72479248046875, 286.73699951171875),
                                                   frame)
        dark_node_mapping.vector_type = 'POINT'
        dark_node_mapping.translation = (0.0, 0.0, 0.0)
        dark_node_mapping.rotation = (0.0, 0.0, 0.0)
        dark_node_mapping.scale = (1.0, 0.05, 1.0)
        self.nodes.link_nodes(object_texture_coordinate, "Object",
                              dark_node_mapping, "Vector")

        rings_node_mapping = self.nodes.create_node('ShaderNodeMapping',
                                                    'Mapping',
                                                    (-76.69708251953125, -29.712936401367188),
                                                    frame)
        rings_node_mapping.vector_type = 'POINT'
        rings_node_mapping.translation = (0.0, 0.0, 0.0)
        rings_node_mapping.rotation = (0.0, 0.0, 0.0)
        rings_node_mapping.scale = (1.0, 0.1, 1.0)
        self.nodes.link_nodes(object_texture_coordinate, "Object",
                              rings_node_mapping, "Vector")

        dark_color_ramp = self.pores_dark(frame, dark_node_mapping)
        noise, rings_color_ramp, rings_mix = self.pores_wood_rings(frame, rings_node_mapping, node_wood_pattern_wave, node_wood_pattern_mix)

        return dark_color_ramp, noise, rings_color_ramp, rings_mix

    def glossy_coat(self,
                    wood_pattern_ramp: bpy.types.ShaderNodeValToRGB):
        frame = self.nodes.create_node('NodeFrame',
                                       'Glossy Coat',
                                       (1189.5881, 1165.8339),
                                       label="Glossy Coat")
        frame.shrink = True

        fresnel = self.nodes.create_node('ShaderNodeFresnel',
                                         'Fresnel',
                                         (-515.9866, -126.2596),
                                         frame)
        fresnel.inputs['IOR'].default_value = 1.450

        node_color_ramp = self.nodes.create_node('ShaderNodeValToRGB',
                                                 'ColorRamp',
                                                 (-280.0497, 43.2715),
                                                 frame)
        color_ramp = node_color_ramp.color_ramp
        color_ramp.interpolation = "LINEAR"
        color_ramp_1 = color_ramp.elements[1]
        color_ramp_1.color = (0.602, 0.602, 0.602, 1.0)
        self.nodes.link_nodes(fresnel, "Fac",
                              node_color_ramp, "Fac")

        node_mix_wave = self.nodes.create_node('ShaderNodeMixRGB',
                                               'Mix',
                                               (-219.8289, -161.1724),
                                               frame)
        node_mix_wave.blend_type = "MIX"
        self.nodes.link_nodes(wood_pattern_ramp, 'Color',
                              node_mix_wave, 'Fac')
        node_mix_wave.inputs['Color1'].default_value = (0.233, 0.233, 0.233, 1.0)
        node_mix_wave.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)

        node_mix = self.nodes.create_node('ShaderNodeMixRGB',
                                          'Mix',
                                          (-0.4312, -16.0930),
                                          frame)
        node_mix.blend_type = "MIX"
        self.nodes.link_nodes(node_color_ramp, 'Color',
                              node_mix, 'Fac')
        node_mix.inputs['Color1'].default_value = (0.0, 0.0, 0.0, 1.0)
        self.nodes.link_nodes(node_mix_wave, 'Color',
                              node_mix, 'Color2')

        return node_mix

    def bump(self,
             wood_rings_noise: bpy.types.ShaderNodeTexNoise,
             alpha_wave: bpy.types.ShaderNodeValToRGB,
             color_wave: bpy.types.ShaderNodeValToRGB,
             dark_noise: bpy.types.ShaderNodeValToRGB):
        frame = self.nodes.create_node('NodeFrame',
                                       'Bump',
                                       (1308.3367, -147.7888),
                                       label="Bump")
        frame.shrink = True

        node_mix_noise = self.nodes.create_node('ShaderNodeMixRGB',
                                                'Mix',
                                                (-551.5355, 3.1031),
                                                frame)
        node_mix_noise.blend_type = "MIX"
        self.nodes.link_nodes(wood_rings_noise, 'Color',
                              node_mix_noise, 'Fac')
        node_mix_noise.inputs['Color1'].default_value = (0.0, 0.0, 0.0, 1.0)
        node_mix_noise.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)

        node_mix_wave = self.nodes.create_node('ShaderNodeMixRGB',
                                               'Mix',
                                               (-340.5406, 19.2297),
                                               frame)
        node_mix_wave.blend_type = "MIX"
        self.nodes.link_nodes(alpha_wave, 'Alpha',
                              node_mix_wave, 'Fac')
        self.nodes.link_nodes(node_mix_noise, 'Color',
                              node_mix_wave, 'Color1')
        self.nodes.link_nodes(color_wave, 'Color',
                              node_mix_wave, 'Color2')

        node_mix_dark = self.nodes.create_node('ShaderNodeMixRGB',
                                               'Mix',
                                               (-390.6692, 207.1184),
                                               frame)
        node_mix_dark.blend_type = "MIX"
        self.nodes.link_nodes(dark_noise, 'Alpha',
                              node_mix_dark, 'Fac')
        node_mix_dark.inputs['Color1'].default_value = (0.0, 0.0, 0.0, 1.0)
        self.nodes.link_nodes(node_mix_wave, 'Color',
                              node_mix_dark, 'Color2')

        node_bump = self.nodes.create_node('ShaderNodeBump',
                                           'Bump',
                                           (26.3358, 65.8390),
                                           frame)
        node_bump.inputs['Strength'].default_value = 0.3
        node_bump.inputs['Distance'].default_value = 0.1
        self.nodes.link_nodes(node_mix_dark, 'Color',
                              node_bump, 'Height')

        return node_bump

    def build_wood_material(self):
        node_tex_coord = self.nodes.create_node('ShaderNodeTexCoord',
                                                'Texture Coordinate',
                                                (-1130.3658, 414.2327))

        node_mapping, node_wave, color_wave, node_mix = self.wood_pattern(node_tex_coord)
        dark_color_ramp, noise, alpha_wave, rings_mix = self.pores(node_tex_coord, node_wave, node_mix)
        node_bump = self.bump(noise, alpha_wave, color_wave, dark_color_ramp)
        glossy_coat = self.glossy_coat(color_wave)

        node_mix_all = self.nodes.create_node('ShaderNodeMixRGB',
                                              'Mix',
                                              (956.2424, 754.7979))
        node_mix_all.blend_type = "MIX"
        self.nodes.link_nodes(dark_color_ramp, 'Alpha',
                              node_mix_all, 'Fac')
        node_mix_all.inputs['Color1'].default_value = (0.121, 0.023, 0.007, 1.0)
        self.nodes.link_nodes(rings_mix, 'Color',
                              node_mix_all, 'Color2')

        node_diffuse = self.nodes.create_node('ShaderNodeBsdfDiffuse',
                                              'Diffuse BSDF',
                                              (1174.4573, 758.0632))
        self.nodes.link_nodes(node_mix_all, 'Color',
                              node_diffuse, 'Color')
        node_diffuse.inputs['Roughness'].default_value = 0.0

        node_glossy = self.nodes.create_node('ShaderNodeBsdfGlossy',
                                             'Glossy BSDF',
                                             (1169.2505, 612.4163))
        node_glossy.distribution = 'BECKMANN'
        node_glossy.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1.0)
        node_glossy.inputs['Roughness'].default_value = 0.0
        self.nodes.link_nodes(node_bump, 'Normal',
                              node_glossy, 'Normal')

        node_mix_shader = self.nodes.create_node('ShaderNodeMixShader',
                                                 'Mix Shader',
                                                 (1416.6094, 767.0349))
        self.nodes.link_nodes(glossy_coat, 'Color',
                              node_mix_shader, 'Fac')
        self.nodes.link_nodes(node_diffuse, 0,
                              node_mix_shader, 1)
        self.nodes.link_nodes(node_glossy, 0,
                              node_mix_shader, 2)

        output = self.nodes.create_node('ShaderNodeOutputMaterial',
                                        'Material Output',
                                        (1666.5558, 746.3076))
        self.nodes.link_nodes(node_mix_shader, 'Shader',
                              output, 'Surface')

def test():
    mat = bpy.data.materials.new("WoodMaterialCekhunen")
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nodes = Nodes(mat.node_tree)
    wood_mat = WoodMaterialCekhunen(nodes)
    wood_mat.build_wood_material()

test()