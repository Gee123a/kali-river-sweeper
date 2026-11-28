"""Writes the 4 hotbar role icons (T_Icon_Role_{Serok,Capit,Ganco,Garuk}.png, 256 px RGBA) to
unity/Assets/_Project/Props/Tools/Icons/ (JC folder; Niki's hotbar references them from there).

    blender -b --factory-startup -P blender/build_icons.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402,F401
from kali_blender import icons  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "unity", "Assets", "_Project", "Props", "Tools", "Icons")
for p in icons.write_role_icons(OUT):
    print("icon", os.path.relpath(p, os.path.dirname(HERE)).replace(os.sep, "/"))
