#!/usr/bin/env python3
"""Cuts Vazirmatn down to just the Persian glyphs build.py uses.

GitHub shows README images as <img>, which cannot load web fonts, so the
font has to be embedded inside each SVG; a subset keeps that to a few KB.
Run again whenever you change Persian text in build.py (needs fonttools).
"""
import os, re
from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "scripts", "build.py"), encoding="utf-8").read()
chars = set(re.findall(r"[؀-ۿ‌٫٬]", src)) | set(" /:.،·")
opts = subset.Options()
opts.flavor = "woff"
opts.layout_features = ["*"]          # keep Persian joining and ligatures
opts.name_IDs = []
opts.notdef_outline = True
font = subset.load_font(os.path.join(ROOT, "fonts", "Vazirmatn-Variable.ttf"), opts)
sub = subset.Subsetter(opts)
sub.populate(text="".join(sorted(chars)))
sub.subset(font)
out = os.path.join(ROOT, "assets", "vazirmatn-subset.woff")
subset.save_font(font, out, opts)
print(len(chars), "glyphs ->", out, os.path.getsize(out), "bytes")
