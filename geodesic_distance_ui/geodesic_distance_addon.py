##### HOW TO INSTALL ADD-ON:
# Go to Edit > Preferences > Add-ons
# Click Install... > Select this file > Enable Add-on


bl_info = {
    "name": "Geodesic Distance Computation",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
import os
import subprocess
from bpy_extras.io_utils import ImportHelper

import potpourri3d as pp3d
import numpy as np


def get_uv_layer(ob):
    uvs = ob.data.uv_layers.get("dists") or ob.data.uv_layers.new(name="dists")
    ob.data.uv_layers.active = uvs

    return uvs

def set_uvs(ob, uv_values):
    uvs = get_uv_layer(ob)
    for face in ob.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            uvs.data[loop_idx].uv = (uv_values[vert_idx, 0], uv_values[vert_idx, 1]) # ie UV coord for each face with vert  me.vertices[vert_idx]

def get_uvs(ob):
    uv_values = np.zeros((len(ob.data.vertices), 2))
    uvs = get_uv_layer(ob)
    for face in ob.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            uv_values[vert_idx, 0] = uvs.data[loop_idx].uv[0]
            uv_values[vert_idx, 1] = uvs.data[loop_idx].uv[1]

    return uv_values

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

def get_selected_vertices():
    # If the current active object is not a mesh, return
    if bpy.context.active_object.type != 'MESH':
        return []

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    ob = bpy.context.active_object
    mesh = ob.data
    selected_verts = [v.index for v in mesh.vertices if v.select]
            
    # bpy.ops.object.mode_set(mode=current_mode)

    return selected_verts


def mesh_poll(self, object):
    return object.type == 'MESH'


source_vertices_id = []

def update_mesh(self, context):
    print("Changed mesh")
    source_vertices_id.clear()
    if bpy.data.materials.get("dist_shader"):
        context.scene.geodist_props.mesh_object.active_material = bpy.data.materials["dist_shader"]

class GeoDistancePropertyGroup(bpy.types.PropertyGroup):
    mesh_object: bpy.props.PointerProperty(name="Mesh", type=bpy.types.Object, poll=mesh_poll, update=update_mesh)


class ComputeDistanceOperator(bpy.types.Operator):
    """Distance Computation Script"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "geodist.compute_operator"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Compute Geodesic Distance"         # Display name in the interface.
    # bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.


    def execute(self, context):
        V = get_mesh_coordinates(context.scene.geodist_props.mesh_object)
        F = get_mesh_faces(context.scene.geodist_props.mesh_object)
        dist = pp3d.compute_distance_multisource(V,F,source_vertices_id)

        uv_values = get_uvs(context.scene.geodist_props.mesh_object)

        uv_values[:, 1] = dist

        set_uvs(context.scene.geodist_props.mesh_object, uv_values)

        return {'FINISHED'}

class SetSourceVerticesOperator(bpy.types.Operator):
    """Add Source Vertices"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "geodist.set_source_vertices"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Add Source Vertices"         # Display name in the interface.

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object and bpy.context.active_object.type == 'MESH'

    def execute(self, context):        # execute() is called when running the operator.
        selected_vertices_ids = get_selected_vertices()

        # subprocess.run("pbcopy", input=str(selected_vertices_ids).encode())

        source_vertices_id.extend(selected_vertices_ids)

        uv_values = np.ones((len(context.scene.geodist_props.mesh_object.data.vertices), 2) , dtype=float)
        uv_values[source_vertices_id, np.zeros(len(source_vertices_id), dtype=int)] = 0

        set_uvs(context.scene.geodist_props.mesh_object, uv_values)


        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class ClearSourceVerticesOperator(bpy.types.Operator):
    """Clear Source Vertices"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "geodist.clear_source_vertices"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Clear Source Vertices"         # Display name in the interface.

    def execute(self, context):        # execute() is called when running the operator.

        source_vertices_id.clear()

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        uv_values = np.ones((len(context.scene.geodist_props.mesh_object.data.vertices), 2) , dtype=float)

        set_uvs(context.scene.geodist_props.mesh_object, uv_values)


        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class GeoDistancePanel(bpy.types.Panel):
    """Geodesic Distance"""
    bl_label = "Geodesic Distance"
    bl_idname = "selector_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Geodesic Distance"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        # METHOD INPUT
        row = layout.row()
        row.label(text="Input", icon='IMPORT')

        layout.prop(context.scene.geodist_props, 'mesh_object')
        layout.operator(SetSourceVerticesOperator.bl_idname)
        layout.operator(ClearSourceVerticesOperator.bl_idname)
        

        # GET SELECTED VERTICES
        row = layout.row()
        row.label(text="Compute", icon='RIGHTARROW_THIN')
        layout.operator(ComputeDistanceOperator.bl_idname)





def register():
    bpy.utils.register_class(GeoDistancePropertyGroup)
    bpy.types.Scene.geodist_props = bpy.props.PointerProperty(type=GeoDistancePropertyGroup)
    bpy.utils.register_class(ComputeDistanceOperator)
    bpy.utils.register_class(SetSourceVerticesOperator)
    bpy.utils.register_class(ClearSourceVerticesOperator)
    bpy.utils.register_class(GeoDistancePanel)

def unregister():
    del bpy.types.Scene.geodist_props
    bpy.utils.unregister_class(ComputeDistanceOperator)
    bpy.utils.unregister_class(SetSourceVerticesOperator)
    bpy.utils.unregister_class(ClearSourceVerticesOperator)
    bpy.utils.unregister_class(GeoDistancePanel)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

    