import os
import sys

########## Run this from Blender text editor to load the add-on code quickly during development

########## Script taken straight from https://b3d.interplanety.org/en/creating-multifile-add-on-for-blender/
 
# Replace by absolute path to your directory (this is only for development)
filesDir = "/Users/emilie/Documents/Work/blender-scripts-demo/geodesic_distance_ui/geodesic_distance_addon"
 
initFile = "__init__.py"
 
if filesDir not in sys.path:
    sys.path.append(filesDir)
 
file = os.path.join(filesDir, initFile)
 
if 'DEBUG_MODE' not in sys.argv:
    sys.argv.append('DEBUG_MODE')
 
exec(compile(open(file).read(), initFile, 'exec'))
 
if 'DEBUG_MODE' in sys.argv:
    sys.argv.remove('DEBUG_MODE')