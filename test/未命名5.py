# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 16:43:14 2024

@author: wly
"""

#!usr/bin/env python
# -*- coding: utf-8 -*-
"""
date：2022/11/17
author：甲戌_Tr
email: liu_xxxi@163.com
"""

import rasterio
from rasterio import features
from shapely.geometry import shape
import geopandas as gpd
from tqdm import tqdm
def raster2polygon(inraster,outshp,nodata=None):
    
    def count_from_zero():
        i = 0
        while True:
            yield i
            i += 1
    
    
    # out_shp = gpd.GeoDataFrame(columns=['DN','geometry'])
    
    with rasterio.open(inraster) as f:
        image = f.read(1)
        img_crs = f.crs
        if nodata is None:
            nodata = f.nodata
        image[image == f.nodata] = nodata
        # f.profile

        # counter = count_from_zero()
        x = list(features.shapes(image, transform=f.transform))
        out_list = [
            (value, shape(coords))
            for coords, value in tqdm(features.shapes(image, transform=f.transform),total=len(features.shapes(image, transform=f.transform)))
            if value != nodata
        ]

        # 转换为 DataFrame
        out_shp = gpd.GeoDataFrame(out_list, columns=['value', 'geometry'])
        
        # i = 0
        # for coords, value in features.shapes(image, transform=f.transform):
        #     if value != nodata:
        #         geom = shape(coords)
        #         out_shp.loc[i] = [value,geom]
        #         i += 1

    out_shp.set_geometry('geometry',inplace=True)
    # out_shp = out_shp.dissolve(by='DN')

    out_shp.to_file(outshp,crs=img_crs)

    return out_shp




ph_tif = r'F:/01beijingword/05 lulc/ISA/ujjj/GAUD_1985_2015.tif'

out_tif = r'F:\PyCharm\pythonProject1\代码\mycode\测试文件\GAUD_1985_2015.shp'


raster2polygon(ph_tif,out_tif)




# [i for i,v in tqdm(enumerate(range(5)),leave=4) if v !=1]






# import inspect
# class Label:
#     def __init__(self) -> None:
#     # 获取调用当前构造函数的帧
#         caller_frame: inspect.FrameType | None = inspect.currentframe().f_back
#         self.line_number:int = caller_frame.f_lineno # 获取行号
# def gotoLine(line:int) -> None:
#     breakpoint(commands=['n', f"j {line}", 'c'])
# pass

# def gotoLabel(obj:Label) -> None:
#     breakpoint(commands=['n', f"j {obj.line_number}", 'c'])
# pass

# Label1 = Label()
# print("hello")
# gotoLabel(Label1)

































