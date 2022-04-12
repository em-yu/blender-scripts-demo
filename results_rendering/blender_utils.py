import bpy
import bmesh
import numpy as np
import os
from mathutils import Matrix, Vector, Euler
from math import pi

MATERIALS_BLEND_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "materials.blend")

def setup_scene(envmap_path=None):

    # Init blender
    bpy.ops.wm.read_homefile()

    # render engine
    # bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 1920 
    bpy.context.scene.render.resolution_y = 1080 
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.view_settings.exposure = 1
    bpy.context.scene.view_settings.gamma = 0.5

    # Environment lighting
    if envmap_path is not None:
        bpy.context.scene.world.use_nodes = True
        node_tex = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        node_tex.image = bpy.data.images.load(envmap_path)
        node_tree = bpy.context.scene.world.node_tree
        # Tweak saturation
        node_hsv = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeHueSaturation")
        node_hsv.inputs[1].default_value = 0.2 # Set saturation
        node_tree.links.new(node_tex.outputs['Color'], node_hsv.inputs['Color'])
        node_tree.links.new(node_hsv.outputs['Color'], node_tree.nodes['Background'].inputs['Color'])

    bpy.ops.object.select_all(action = 'SELECT')
    bpy.ops.object.delete()

# Add a turntable animation to all objects in the scene (except cameras and emptys)
def add_turntables(nb_frames=240):
    
    scene = bpy.context.scene
    # Render parameters
    scene.frame_end = nb_frames
    scene.render.fps = 24

    # Create empty
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty = bpy.context.object
    bpy.ops.collection.objects_remove_all()
    # add it to the default collection
    bpy.data.collections['Collection'].objects.link(empty)

    # Set keyframes for rotation
    empty.keyframe_insert(data_path="rotation_euler", frame=1)
    empty.rotation_euler = Euler((0, 0, 2 * pi), 'XYZ')
    empty.keyframe_insert(data_path="rotation_euler", frame=nb_frames + 1)

    fcurves = empty.animation_data.action.fcurves
    for fcurve in fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'LINEAR'

    # Parent all non camera objects of the scene to the empty
    for ob in bpy.data.objects:
        if ob.type != 'CAMERA' and ob.type != 'EMPTY':
            ob.parent = empty

            

def get_or_load_mat(mat_name):
    if bpy.data.materials.get(mat_name):
        return bpy.data.materials[mat_name]
    else:
        return load_mat(mat_name)

def load_mat(mat_name):
    path = MATERIALS_BLEND_FILE + "\\Material\\"
    bpy.ops.wm.append(filename=mat_name, directory=path)
    mat = bpy.data.materials.get(mat_name)
    return mat

def create_camera(name, position, rotation):
    bpy.ops.object.camera_add(location=position)
    bpy.context.object.name = name
    bpy.context.object.rotation_euler = Euler(rotation, 'XYZ')

    return bpy.context.object

def add_mesh(V, F, name, collection='Collection'):
    mesh = bpy.data.meshes.new(name)
    new_obj = bpy.data.objects.new(name, mesh)
    col = bpy.data.collections.get(collection)
    if col is None:
        col = bpy.data.collections.new(collection)
    col.objects.link(new_obj)
    V = list(map(tuple, V))
    F = list(map(tuple, F))
    mesh.from_pydata(V, [], F)

    return new_obj

def set_collection(ob, new_collection):
    old_coll = ob.users_collection #list of all collection the obj is in

    new_collection.objects.link(ob) #link obj to scene

    for col in old_coll: #unlink from all  precedent obj collections
        col.objects.unlink(ob)

def hide_col(collection):
    collection.hide_viewport = True
    collection.hide_render = True

def show(collection):
    collection.hide_viewport = False
    collection.hide_render = False


def hide_all_in_collection(col):
    for ob in col.objects:
        ob.hide_render = True

def set_per_face_colors(ob, colors_by_face, label):

    color_layer = ob.data.vertex_colors.get(label) or ob.data.vertex_colors.new(name=label)

    for poly, color in zip(ob.data.polygons, colors_by_face):
        # for idx in poly.loop_indices:
        for i, index in enumerate(poly.vertices):
            loop_index = poly.loop_indices[i]
            color_layer.data[loop_index].color[0] = color[0]
            color_layer.data[loop_index].color[1] = color[1]
            color_layer.data[loop_index].color[2] = color[2]
            color_layer.data[loop_index].color[3] = 1 # set alpha

def mark_sharp(ob, vertex_is_sharp):
    # Make sure all mesh elements are deselected first
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    for e in ob.data.edges:
        if np.all(vertex_is_sharp[e.vertices]):
            # Mark as sharp
            e.select = True
        else:
            e.select = False
    
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.mark_sharp(clear=True)
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.mark_sharp()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Add modifier to render sharp edges correctly
    bpy.ops.object.modifier_add(type='EDGE_SPLIT')
    bpy.context.object.modifiers["EdgeSplit"].use_edge_angle = False

    # Shade smooth
    ob.select_set(True)
    bpy.ops.object.shade_smooth()
    ob.select_set(False)


def mark_seam(ob, vertex_is_seam):
    # Make sure all mesh elements are deselected first
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Mark segmentation seams as UV seams
    for e in ob.data.edges:
        if np.all(vertex_is_seam[e.vertices]):
            # Mark as sharp
            e.select = True
        else:
            e.select = False

    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.mesh.select_all(action='INVERT')
    # bpy.ops.mesh.mark_sharp(clear=True)
    bpy.ops.mesh.mark_seam(clear=True)
    bpy.ops.mesh.select_all(action='INVERT')
    # bpy.ops.mesh.mark_sharp()
    bpy.ops.mesh.mark_seam()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def uv_unwrap(ob):
    # Make sure all mesh elements are deselected first
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all()
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')