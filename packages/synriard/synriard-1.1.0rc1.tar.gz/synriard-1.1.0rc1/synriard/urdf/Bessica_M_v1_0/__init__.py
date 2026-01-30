import os
from types import SimpleNamespace

# Get the absolute path to THIS directory
_MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

# Module-level urdf attribute for when variant is None or empty string
urdf = os.path.join(_MODULE_PATH, "Bessica_M_v1_0.urdf")

Bessica_M_v1_0 = SimpleNamespace()
Bessica_M_v1_0.urdf = os.path.join(_MODULE_PATH, "Bessica_M_v1_0.urdf")