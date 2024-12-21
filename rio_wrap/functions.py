# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 10:41:42 2024

@author: wly
"""


import rasterio




def create_raster(**kwargs):
    memfile = rasterio.MemoryFile()
    return memfile.open(**kwargs)