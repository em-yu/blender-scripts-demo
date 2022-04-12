##### HOW TO INSTALL ADD-ON:
# Go to Edit > Preferences > Add-ons
# Click Install... > Select this file > Enable Add-on


bl_info = {
    "name": "Vertex Selector",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
import os
import subprocess
from bpy_extras.io_utils import ImportHelper

def get_selected_vertices():
    # If the current active object is not a mesh, return
    if bpy.context.active_object.type != 'MESH':
        return []

    current_mode = bpy.context.active_object.mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    ob = bpy.context.active_object
    mesh = ob.data
    selected_verts = [v.index for v in mesh.vertices if v.select]
            
    bpy.ops.object.mode_set(mode=current_mode)

    return selected_verts


class LoadObjMeshOperator(bpy.types.Operator, ImportHelper):
    """Obj Mesh Loading Script"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "selector.load_mesh_operator"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Load Meshes"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.


    filter_glob : bpy.props.StringProperty(
            default="*.obj",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    files : bpy.props.CollectionProperty(name="Mesh Files", description="OBJ files to load", type=bpy.types.OperatorFileListElement)
    directory : bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        for file in self.files:
            path = os.path.join(self.directory, file.name)
            print("import %s" % path)
            # Load mesh file (important to keep vertices order! => split_mode = OFF)
            bpy.ops.import_scene.obj(filepath=path, split_mode='OFF')
            ob = bpy.context.selected_objects[0]
            ob.hide_set(True)

        return {'FINISHED'}

class GetSelectedVerticesOperator(bpy.types.Operator):
    """Selected Vertices Copy Script"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "selector.get_selected_vertices"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Get Selected Vertices"         # Display name in the interface.

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object and bpy.context.active_object.type == 'MESH'

    def execute(self, context):        # execute() is called when running the operator.
        selected_vertices_ids = get_selected_vertices()
        print(selected_vertices_ids)

        subprocess.run("pbcopy", input=str(selected_vertices_ids).encode())


        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class SelectorPanel(bpy.types.Panel):
    """Vertex Selector UI Panel"""
    bl_label = "Vertex Selector Panel"
    bl_idname = "selector_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vertex Selector"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        # LOAD INPUT
        row = layout.row()
        row.label(text="Input", icon='IMPORT')
        
        layout.operator(LoadObjMeshOperator.bl_idname)

        # GET SELECTED VERTICES
        row = layout.row()
        row.label(text="Get selected", icon='DUPLICATE')
        layout.operator(GetSelectedVerticesOperator.bl_idname)


def register():
    bpy.utils.register_class(LoadObjMeshOperator)
    bpy.utils.register_class(GetSelectedVerticesOperator)
    bpy.utils.register_class(SelectorPanel)

def unregister():
    del bpy.types.Scene.selector_custom_props
    bpy.utils.unregister_class(LoadObjMeshOperator)
    bpy.utils.unregister_class(GetSelectedVerticesOperator)
    bpy.utils.unregister_class(SelectorPanel)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

    