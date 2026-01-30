import os
from types import SimpleNamespace

# Get the absolute path to THIS directory
_MODULE_PATH = os.path.dirname(os.path.abspath(__file__))



Bessica_M_v1_0 = SimpleNamespace()
Bessica_M_v1_0.xml = os.path.join(_MODULE_PATH, "Bessica_M_v1_0.xml")

Bessica_M_v1_0_interactive = SimpleNamespace()
Bessica_M_v1_0_interactive.xml = os.path.join(_MODULE_PATH, "Bessica_M_v1_0_interactive.xml")
