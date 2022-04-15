##### HOW TO INSTALL ADD-ON:
# Go to Edit > Preferences > Add-ons
# Click Install... > Select this file > Enable Add-on


bl_info = {
    "name": "Object Transform Copy",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy
import os
import subprocess
from bpy_extras.io_utils import ImportHelper

def copy_location_rotation(ob, separator=";"):
    loc = ob.location
    rot = ob.rotation_euler
    txt = f"({loc.x:.5f}, {loc.y:.5f}, {loc.z:.5f}){separator}({rot.x:.5f}, {rot.y:.5f}, {rot.z:.5f})"
    subprocess.run("pbcopy", input=txt.encode())


class LoadObjMeshOperator(bpy.types.Operator, ImportHelper):
    """Obj Mesh Loading Script"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "transform_copy.load_mesh_operator"        # Unique identifier for buttons and menu items to reference.
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
            bpy.ops.import_scene.obj(filepath=path)
            ob = bpy.context.selected_objects[0]
            ob.hide_set(True)

        return {'FINISHED'}

class LocRotCopyOperator(bpy.types.Operator):
    """Object Transform Copy Script"""          # Use this as a tooltip for menu items and buttons.
    bl_idname = "transform_copy.copy_loc_rot"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Copy Object Location/Rotation"         # Display name in the interface.

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object

    def execute(self, context):        # execute() is called when running the operator.
        copy_location_rotation(context.object)

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class TransformCopyPanel(bpy.types.Panel):
    """Transform Copy UI Panel"""
    bl_label = "Transform Copy Panel"
    bl_idname = "transform_copy_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Transform Copy"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        # LOAD INPUT
        row = layout.row()
        row.label(text="Input", icon='IMPORT')
        
        layout.operator(LoadObjMeshOperator.bl_idname)

        # GET SELECTED VERTICES
        row = layout.row()
        row.label(text="Copy Transform", icon='DUPLICATE')
        layout.operator(LocRotCopyOperator.bl_idname)


def register():
    bpy.utils.register_class(LoadObjMeshOperator)
    bpy.utils.register_class(LocRotCopyOperator)
    bpy.utils.register_class(TransformCopyPanel)

def unregister():
    bpy.utils.unregister_class(LoadObjMeshOperator)
    bpy.utils.unregister_class(LocRotCopyOperator)
    bpy.utils.unregister_class(TransformCopyPanel)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()

    