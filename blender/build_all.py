"""Rebuild every GLB in ./assets from a terminal:

    blender --background --factory-startup --python blender/build_all.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import arch
import city
import lamp
import road
import rocks

for mod in (arch, lamp, road, rocks, city):
    print(mod.__name__, mod.build()[0])
