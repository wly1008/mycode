# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 16:39:11 2024

@author: wly
"""
import os, sys, rasterio
import pandas as pd
import numpy as np
import mycode.arcmap as ap
from mycode.rio_wrap import unify, clip, reproject
from os.path import join



os.chdir(r'F:\PyCharm\pythonProject1\代码\mycode\测试文件')





# ph_src = r'F:/PyCharm/pythonProject1/代码/mycode/测试文件/源数据/110_40_1_5_5.tif'

# ph_dst = r'F:/PyCharm/pythonProject1/代码/mycode/测试文件/源数据/111.3_38.6_1_5_5.tif'

ph_src = r'F:/PyCharm/pythonProject1/代码/mycode/测试文件/源数据/1990-5km-tiff.tif'

ph_dst = r'F:/PyCharm/pythonProject1/代码/mycode/测试文件/源数据/eva_2.tif'


out_dir = r'F:\PyCharm\pythonProject1\代码\mycode\测试文件\rio_wrap\2411'

out_ph = join(out_dir, 'unity2.tif')
# src = rasterio.open(ph_src)
# src.count
unify(ph_src, ph_dst, out_ph,nodata=255,Double_operation=True,how=6)

# mode='touch'
# mode='rio'
# # mode = 'round'
# out_ph = join(out_dir, 'clip2.tif')
# clip(ph_src, ph_dst, out_ph,mode=mode,crop=0,nodata=1,dtype=np.int32)

with rasterio.open(out_ph) as src:
    arr = src.read()
    profile = src.profile

































