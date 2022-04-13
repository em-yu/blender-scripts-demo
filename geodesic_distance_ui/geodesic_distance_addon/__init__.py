bl_info = {
    "name": "Geodesic Distance Computation",
    "blender": (2, 80, 0),
    "category": "Object",
}
  
import sys
import importlib

########## Script adapted from https://b3d.interplanety.org/en/creating-multifile-add-on-for-blender/

# Add here any other module you need to register/reload
modulesNames = ['geodesic_distance_addon_ui', 'geodesic_project.compute_geodesic_distance']
 
modulesFullNames = {}
for currentModuleName in modulesNames:
    if 'DEBUG_MODE' in sys.argv:
        modulesFullNames[currentModuleName] = ('{}'.format(currentModuleName))
    else:
        modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))

# For some reason running reload twice is necessary for changes in 'geodesic_project' module to be loaded
for i in range(2):
    for currentModuleFullName in modulesFullNames.values():
        if currentModuleFullName in sys.modules:
            importlib.reload(sys.modules[currentModuleFullName])
        else:
            globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
            setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)
 
def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()
 
def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
 
if __name__ == "__main__":
    register()

