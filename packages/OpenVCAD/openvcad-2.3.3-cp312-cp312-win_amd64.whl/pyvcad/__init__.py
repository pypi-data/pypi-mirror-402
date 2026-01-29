"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'openvcad.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

import os
from pyvcad.pyvcad import *

package_dir = os.path.dirname(__file__)
default_materials_path = os.path.join(package_dir, "configs", "default.json")
default_materials = pyvcad.MaterialDefs(default_materials_path)
j750_materials_path = os.path.join(package_dir, "configs", "j750.json")
j750_materials = pyvcad.MaterialDefs(j750_materials_path)
