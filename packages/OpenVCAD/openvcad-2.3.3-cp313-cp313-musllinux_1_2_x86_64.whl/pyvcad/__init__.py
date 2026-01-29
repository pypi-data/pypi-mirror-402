

import os
from pyvcad.pyvcad import *

package_dir = os.path.dirname(__file__)
default_materials_path = os.path.join(package_dir, "configs", "default.json")
default_materials = pyvcad.MaterialDefs(default_materials_path)
j750_materials_path = os.path.join(package_dir, "configs", "j750.json")
j750_materials = pyvcad.MaterialDefs(j750_materials_path)
