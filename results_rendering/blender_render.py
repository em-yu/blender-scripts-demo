import bpy
import sys
import math
import os
import argparse
import re
# import shutil

# Add current directory to system path to be able to import scripts with python
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from blender_utils import hide_all_in_collection

ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__))
OUT_FOLDER = os.path.join(ROOT_FOLDER, 'out')


def render(output_path, camera, animation=False, resolution=1080, fps=24, frame_start=None, frame_end=None, ffmpeg=True):
    # output_path += '/'
    bpy.data.scenes['Scene'].render.filepath = output_path
    bpy.data.scenes['Scene'].camera = camera

    bpy.data.scenes['Scene'].render.resolution_x = int(bpy.data.scenes['Scene'].render.resolution_x * resolution / bpy.data.scenes['Scene'].render.resolution_y)
    bpy.data.scenes['Scene'].render.resolution_y = resolution

    initial_frame_end = bpy.data.scenes['Scene'].frame_end
    initial_frame_start = bpy.data.scenes['Scene'].frame_start

    if animation:
        bpy.data.scenes['Scene'].render.filepath += '/frame'

        if frame_start is not None:
            bpy.data.scenes['Scene'].frame_start = frame_start

        if frame_end is not None:
            bpy.data.scenes['Scene'].frame_end = frame_end


    if fps < bpy.data.scenes['Scene'].render.fps:
        step = bpy.data.scenes['Scene'].render.fps // fps
        bpy.data.scenes['Scene'].frame_step = step

    bpy.ops.render.render(write_still = True, animation=animation)

    # Put back values
    bpy.data.scenes['Scene'].frame_end = initial_frame_end
    bpy.data.scenes['Scene'].frame_start = initial_frame_start

    if ffmpeg:
        output_video_path = os.path.join(output_path, os.pardir, os.path.basename(output_path) + '.mp4')
        command = f"ffmpeg -f lavfi -i color=c=white:s={bpy.data.scenes['Scene'].render.resolution_x}x{bpy.data.scenes['Scene'].render.resolution_y}:r={fps} -pattern_type glob -framerate {fps} -i '{output_path}/*.png' -vcodec libx264 -filter_complex '[0:v][1:v]overlay=shortest=1,format=yuv420p[out]' -map '[out]' -r 24 {output_video_path}"
        print(command)
        stream = os.popen(command).read()

        # Uncomment to have the frames deleted from disk automatically
        # shutil.rmtree(output_path)

def compute_frame_bounds_turntables(initial_frame_start, initial_frame_end, rotation_start=0, rotation_end=360):
    # Adjust start/end frames
    frames_per_degree = (initial_frame_end - initial_frame_start) / 360
    frame_start = initial_frame_start
    frame_end = initial_frame_end
    if rotation_start != 0:
        frame_start = max(1, math.floor(rotation_start * frames_per_degree))
        print("starting at frame", frame_start)
    if rotation_end != 360:
        print(rotation_end, frames_per_degree)
        frame_end = min(initial_frame_end, math.ceil(rotation_end * frames_per_degree))
        print("ending at frame", frame_end)
    return frame_start, frame_end

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--blend-file', help='Name of the blend file', type=str, default=None, required=True)
    parser.add_argument('--out-folder', help='Name of the output folder', type=str, default=None, required=False)
    parser.add_argument('--materials', help='Name of the material(s) to load. They should be defined in the blend file.', type=str, default=[], required=False, nargs='+')
    parser.add_argument('-m', '--mesh', help='Pattern to select mesh(es)', type=str, default=".+")
    parser.add_argument('--turntables', help='Render turntable animations', dest='turntables', action='store_true', default=False)
    parser.add_argument('--ffmpeg', help='Create videos with ffmpeg', dest='ffmpeg', action='store_true', default=False)
    parser.add_argument('-r', '--res', help='Image resolution', dest='resolution', type=int, default=1080)
    parser.add_argument('--fps', help='FPS (probably better to choose a divisor/multiple of 24)', dest='fps', type=int, default=24)
    parser.add_argument('--rot', help='How many degrees of rotation (default = 360, full turn)', dest='rotation', type=int, default=360)
    parser.add_argument('--rot-start', help='Angle of start of rotation (degrees, default = 0)', dest='rotation_start', type=int, default=0)

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv
    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    args = parser.parse_args(argv)

    blend_file_path = os.path.join(OUT_FOLDER, f"{args.blend_file}.blend")

    base_path = OUT_FOLDER

    if args.out_folder is None:
        out_path = os.path.join(base_path, args.blend_file)
    else:
        out_path = os.path.join(base_path, args.out_folder)
    

    bpy.ops.wm.open_mainfile(filepath=blend_file_path)

    # For each top level collection (= each mesh to render), Ignoring the default collection
    all_collections = [c for c in bpy.data.scenes['Scene'].collection.children if len(c.objects) > 0 and c.name != 'Collection']

    print("Rendering collections:")
    print(all_collections)


    for collection in all_collections:
        mesh_name = collection.name
        if re.match(args.mesh, mesh_name):
            # - Hide all other collections
            for c in all_collections:
                c.hide_render = True

            collection.hide_render = False

            cameras = [obj for obj in collection.objects if obj.type == 'CAMERA']

            res_objects = [ob for ob in collection.objects if re.match('.+_result', ob.name)]
            hide_all_in_collection(collection)

            # - For each camera
            for cam_idx, camera in enumerate(cameras):
                # For turntables 1 camera is enough
                if args.turntables and cam_idx > 0:
                    break

                for idx, ob in enumerate(res_objects):

                    ob.hide_render = False

                    out_file_suffix = f"_{idx}" if len(res_objects) > 1 else ""

                    if len(args.materials) == 0:
                        args.materials = ["shiny"]

                    for material in args.materials:
                        if bpy.data.materials.get(material):
                            ob.active_material = bpy.data.materials[material]
                        elif material == 'default':
                            print(f"Using default material to render {ob.active_material}")

                        frame_start, frame_end = compute_frame_bounds_turntables(
                            bpy.data.scenes['Scene'].frame_start,
                            bpy.data.scenes['Scene'].frame_end,
                            rotation_start=args.rotation_start,
                            rotation_end=args.rotation
                        )

                        render(
                            os.path.join(out_path, f"{mesh_name}_{cam_idx}{out_file_suffix}_{material}"), 
                            camera, 
                            animation=args.turntables, 
                            resolution=args.resolution, 
                            fps=args.fps,
                            frame_start=frame_start,
                            frame_end=frame_end,
                            ffmpeg=args.ffmpeg) 

                    ob.hide_render = True                    

