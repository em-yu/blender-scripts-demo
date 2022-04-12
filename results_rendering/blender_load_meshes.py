

import bpy
import numpy as np
import sys
import math
import os
import csv
import argparse
import re

# Add current directory to system path to be able to import scripts with python
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from mesh_properties_io import unpack_mesh_properties
from blender_utils import *

ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__))
MESHES_FOLDER = os.path.join(ROOT_FOLDER, 'meshes')
OUT_FOLDER = os.path.join(ROOT_FOLDER, 'out')
BLENDER_CAMERA_DATA_PATH = os.path.join(ROOT_FOLDER, 'data', 'blender_cameras.csv')

def load_exported_ply_result(ply_file):

    # Load mesh file
    bpy.ops.import_mesh.ply(filepath=ply_file)
    ob = bpy.context.object

    ob.rotation_euler[0] = math.radians(90) # Correct axis orientations

    mesh = ob.data

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply() # Apply all transforms

    sharpness_by_vertex, vertex_is_seam, label_by_poly, degree_by_poly = unpack_mesh_properties(mesh)
    label_color_layer = mesh.vertex_colors['Col']

    set_per_face_colors(ob, np.column_stack([label_by_poly, degree_by_poly, np.zeros(len(label_by_poly))]), label_color_layer.name)

    mark_sharp(ob, sharpness_by_vertex)
    mark_seam(ob, vertex_is_seam)

    # Shade smooth
    bpy.ops.object.shade_smooth()

    # UVs
    uv_unwrap(ob)

    bpy.ops.object.select_all(action='DESELECT')

    # MATERIALS
    # All materials will be loaded from a materials.blend file located in the same folder

    # Set default material
    ob.active_material = get_or_load_mat("rainbow-labels")


    return ob


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--mesh', help='Pattern to select sketch(es)', type=str, default=".+")
    parser.add_argument('--blend-file', help='Name of the output blend file', type=str, default=None)
    parser.add_argument('--turntables', help='Prepare for turntable animations', dest='turntables', action='store_true', default=False)
    parser.add_argument('--materials', help='Name of the material(s) to load. They should be defined in data/materials.blend file.', type=str, default=[], required=False, nargs='+')


    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv
    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    args = parser.parse_args(argv)


    result_meshes_folder = MESHES_FOLDER

    blend_file_name = "all_meshes"

    if args.blend_file is not None:
        blend_file_name = args.blend_file

    blend_file_path = os.path.join(OUT_FOLDER, f"{blend_file_name}.blend")

    # Init blender
    setup_scene(os.path.join(ROOT_FOLDER, 'data/interior.exr'))




    camera_data_per_mesh = {}
    with open(BLENDER_CAMERA_DATA_PATH, mode='r', encoding='utf-8-sig') as csv_file:
        metadata = csv.DictReader(csv_file, delimiter=";")
        for row in metadata:
            camera_data_per_mesh[row['mesh_name']] = row


    files = []
    for item in os.listdir(result_meshes_folder):
        if os.path.isfile(os.path.join(result_meshes_folder, item)) and os.path.splitext(item)[1] == '.ply' and re.match(args.mesh, item):
            files.append(item)

    for f in sorted(files):

        mesh_name, extension = os.path.splitext(f)

        if mesh_name in camera_data_per_mesh:
            camera_data = camera_data_per_mesh[mesh_name]
        else:
            camera_data = None


        # Create a collection with the name of the mesh
        collection = bpy.data.collections.new(mesh_name)
        bpy.context.scene.collection.children.link(collection)

        # Position camera
        if camera_data is not None:
            for i in [1,2]:
                cam1_loc = eval(camera_data[f'cam{i}_loc'])
                cam1_rot = eval(camera_data[f'cam{i}_rot'])

                cam1_obj = create_camera(f"{mesh_name}_camera{i}", cam1_loc, cam1_rot)
                set_collection(cam1_obj, collection)
        else:
            # Create a default camera
            cam_obj = create_camera(f"{mesh_name}_camera", (0, 0, 0.5), (0, 0, 0))
            set_collection(cam_obj, collection)

        # Load mesh
        result_mesh_path = os.path.join(result_meshes_folder, f)
        mesh_object = load_exported_ply_result(result_mesh_path)
        name = f"{mesh_name}_result"
        mesh_object.name = name
        set_collection(mesh_object, collection)

        # Add more materials
        for material_name in args.materials:
            mesh_object.data.materials.append(get_or_load_mat(material_name))

        # Hide collection so that the blender file is easier to navigate
        hide_col(collection)

        bpy.ops.wm.save_mainfile(filepath=blend_file_path)

    if args.turntables:
        add_turntables(nb_frames=240)

    bpy.ops.wm.save_mainfile(filepath=blend_file_path)