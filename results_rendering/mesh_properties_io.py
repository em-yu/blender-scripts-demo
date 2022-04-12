import numpy as np

####################################

# Sample code for mesh exporting from Python to ply format
# Commented in case meshio not available

# import meshio

# def export_to_ply(V, F, filename, vertex_colors=None):

#     points_data = {}
#     if vertex_colors is not None:
#         points_data['red'] = (vertex_colors[:, 0] * 255).astype(np.uint8)
#         points_data['green'] = (vertex_colors[:, 1] * 255).astype(np.uint8)
#         points_data['blue'] = (vertex_colors[:, 2] * 255).astype(np.uint8)

#     mesh = meshio.Mesh(
#         V,
#         cells = [("triangle", F.astype(np.int32))], point_data=points_data)

#     mesh.write(filename)

####################################


# Application dependent IO code
# These 2 functions can be adapted to pack/unpack any per-vertex data needed for rendering

# In this example application I pack into vertex colors 4 properties:
# - R channel: vertex label (with 0 representing no label)
# - G channel: another per-vertex label (specifically, which degree is the surface model for this vertex)
# - B channel: should this vertex be marked as seam? (>=0.5) and shaded as a sharp edge? (>=1.0) (Note: any sharp edge vertex is necessarily a seam vertex)

# Packing data into RGB channels for ply export
def pack_mesh_properties_to_rgb(labels, model_degrees, is_seam, is_sharp):
    seam_marker = np.zeros(len(labels))
    seam_marker[is_seam] = 0.5
    seam_marker[is_sharp] = 1

    return np.column_stack([
                labels / np.max(labels),
                model_degrees / 4,
                seam_marker])

# Unpacking data from blender mesh data (after loading the ply file into blender)
def unpack_mesh_properties(blender_mesh):

    color_layer = blender_mesh.vertex_colors['Col']

    sharpness_by_vertex = np.zeros(len(blender_mesh.vertices), dtype=bool)
    vertex_is_seam = np.zeros(len(blender_mesh.vertices), dtype=bool)

    label_by_poly = []
    degree_by_poly = []

    for poly in blender_mesh.polygons:
        # Find out the color of this face
        label = 0
        degree = 0
        for i, index in enumerate(poly.vertices):
            loop_index = poly.loop_indices[i]
            if color_layer.data[loop_index].color[0] > 0:
                label = color_layer.data[loop_index].color[0]
                degree = color_layer.data[loop_index].color[1]

            sharpness_by_vertex[index] = color_layer.data[loop_index].color[2] > 0.5
            vertex_is_seam[index] = color_layer.data[loop_index].color[2] > 0
            
        label_by_poly.append(label)
        degree_by_poly.append(degree)

    return sharpness_by_vertex, vertex_is_seam, label_by_poly, degree_by_poly