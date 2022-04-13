

import potpourri3d as pp3d
import numpy as np



def get_mesh_coordinates(ob):
    count = len(ob.data.vertices)
    V = np.empty(count * 3)
    ob.data.vertices.foreach_get("co", V)
    V.shape = (count, 3)
    return V

def get_mesh_faces(ob):
    count = len(ob.data.vertices)
    F = np.empty((0, 3), dtype=int)
    for p in ob.data.polygons:
        F = np.row_stack([F, p.vertices])
    return F

def compute(ob, sources):
    V = get_mesh_coordinates(ob)
    F = get_mesh_faces(ob)
    dist = pp3d.compute_distance_multisource(V,F,sources)
    return dist