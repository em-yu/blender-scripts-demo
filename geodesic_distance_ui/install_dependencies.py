import subprocess
import sys
import os

######### This script must be run from Blender once before installing the geodesic_distance_addon
# - Open Blender
# - Go to "Scripting" view (in the top bar, the default is "Layout", the scripting tab is towards the right)
# - In the right empty panel > Top menu > Text > Open > Select this file from explorer
# - Click the little "Play" icon (it may be further to the right of the top menu)
 
# path to python.exe (MAY DEPEND ON OS / BLENDER VERSION)
python_exe = sys.executable
 
# upgrade pip
subprocess.call([python_exe, "-m", "ensurepip"])
subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
 
# install required packages
subprocess.call([python_exe, "-m", "pip", "install", "potpourri3d"])