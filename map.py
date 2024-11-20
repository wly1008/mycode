# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 08:51:29 2024

@author: wly
"""

from matplotlib import font_manager
from matplotlib.patches import ConnectionPatch
import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
from mycode import data
import mycode.codes as cd
import os
import numpy as np
import shapefile as shp
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import LineCollection
from shapefile import Reader

dir_data = os.path.abspath(os.path.dirname(data.__file__))

def font(fontname='time_song'):
    
    dic_font = {0:'time_song', 1:'Times New Roman'}
    
    fontname = dic_font.get(fontname,fontname)
    if fontname == 'time_song':
        # 使用自定义字体，英文数字符号为Times New Roman(主字体)，中文为宋体(补充字体)
        font_manager.fontManager.addfont(dir_data + os.sep + r'font/time_song.ttf') 
    plt.rcParams['font.sans-serif'] = fontname



def add_scalebar(ax,length,loc_x=0.05, loc_y=0.05,fontsize=12, size=None,lw=1):
    '''
    ax: 坐标轴
    lon0: 经度
    lat0: 纬度
    length: 长度 (Km)
    size: 控制粗细和距离的 (km),默认为length的3%
    '''
    length = length*1000
    if size is None:
        size = length*0.03
    else:
        size = size*1000
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    ylen = maxy - miny
    xlen = maxx - minx
    lon0 = xlen*loc_x + minx
    lat0 = ylen*loc_y + miny
    # style 3
    ax.hlines(y=lat0,  xmin = lon0, xmax = lon0+length, colors="black", ls="-", lw=lw, label='%d km' % (length))
    ax.vlines(x = lon0, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    ax.vlines(x = lon0+length/4, ymin = lat0-size/3*2, ymax = lat0+size/3*2, colors="black", ls="-", lw=lw/2)
    ax.vlines(x = lon0+length/2, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    ax.vlines(x = lon0+length/4*3, ymin = lat0-size/3*2, ymax = lat0+size/3*2, colors="black", ls="-", lw=lw/2)
    ax.vlines(x = lon0+length, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    
    
    ax.text(lon0+length,lat0+size+size*1,'%d km' % (length/1000),ha = 'center',fontsize=fontsize)
    ax.text(lon0+length/2,lat0+size+size*1,'%d' % (length/2000),ha = 'center',fontsize=fontsize)
    ax.text(lon0,lat0+size+size*1,'0',ha = 'center',fontsize=fontsize)
    # ax.text(lon0+length*1.1,lat0+size+size*1,'km',horizontalalignment = 'left')
    


def add_scalebar1(ax,length,loc_x=0.05, loc_y=0.05, size=None,lw=1):
    '''
    ax: 坐标轴
    lon0: 经度
    lat0: 纬度
    length: 长度 (Km)
    size: 控制粗细和距离的 (km),设为None则为length的3%
    '''
    length = length*1000
    if size is None:
        size = length*0.03
    else:
        size = size*1000
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    ylen = maxy - miny
    xlen = maxx - minx
    lon0 = xlen*loc_x + minx
    lat0 = ylen*loc_y + miny
    # style 3
    ax.hlines(y=lat0,  xmin = lon0, xmax = lon0+length, colors="black", ls="-", lw=lw, label='%d km' % (length))
    ax.vlines(x = lon0, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    # ax.vlines(x = lon0+length/4, ymin = lat0-size/3*2, ymax = lat0+size/3*2, colors="black", ls="-", lw=lw/2)
    # ax.vlines(x = lon0+length/2, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    # ax.vlines(x = lon0+length/4*3, ymin = lat0-size/3*2, ymax = lat0+size/3*2, colors="black", ls="-", lw=lw/2)
    ax.vlines(x = lon0+length, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    
    
    
    # ax.text(lon0+length,lat0+size+size*1,'%d' % (length/1000),horizontalalignment = 'center')
    ax.text(lon0+length/2,lat0+size+size*1,'%dkm' % (length/1000),horizontalalignment = 'center')
    # ax.text(lon0,lat0+size+size*1,'0',horizontalalignment = 'center')
    # ax.text(lon0+length*0.6,lat0+size+size*1,'km',horizontalalignment = 'left')
    
def add_north(ax,  loc_x=0.07,loc_y=0.95, labelsize=18, width=0.03, height=0.05, pad=0.1):
    """
    画一个比例尺带'N'文字注释
    主要参数如下
    :param ax: 要画的坐标区域 Axes实例 plt.gca()获取即可
    :param labelsize: 显示'N'文字的大小
    :param loc_x: 以文字下部为中心的占整个ax横向比例
    :param loc_y: 以文字下部为中心的占整个ax纵向比例
    :param width: 指南针占ax比例宽度
    :param height: 指南针占ax比例高度
    :param pad: 文字符号占ax比例间隙
    :return: None
    """
    import matplotlib.patches as mpatches
    minx, maxx = ax.get_xlim()
    miny, maxy = ax.get_ylim()
    ylen = maxy - miny
    xlen = maxx - minx
    
    
    height = height * xlen / ylen

    
    left = [minx + xlen*(loc_x - width*.5), miny + ylen*(loc_y - pad)]
    right = [minx + xlen*(loc_x + width*.5), miny + ylen*(loc_y - pad)]
    top = [minx + xlen*loc_x, miny + ylen*(loc_y - pad + height)]
    center = [minx + xlen*loc_x, left[1] + (top[1] - left[1])*.4]
    triangle = mpatches.Polygon([left, top, right, center], color='k')
    
    
    
    
    ax.text(s='N',
            x=minx + xlen*loc_x,
            y=miny + ylen*(loc_y - pad + height),
            fontsize=labelsize,
            horizontalalignment='center',
            verticalalignment='bottom')
    ax.add_patch(triangle)

def get_crs(gdf):
    import warnings
    warnings.filterwarnings('ignore')

    crs_dict = gdf.crs.to_dict()
    globe = ccrs.Globe(ellipse=crs_dict.get('ellps','WGS84'))
    if crs_dict['proj'] == 'longlat':
        return ccrs.PlateCarree(crs_dict.get('lon_0',0), globe)
    switch = {
        'aea': ccrs.AlbersEqualArea(central_longitude=crs_dict['lon_0'], central_latitude=crs_dict['lat_0'],
                                    false_easting = crs_dict['x_0'], false_northing=crs_dict['y_0'],
                                    standard_parallels=(crs_dict['lat_1'], crs_dict['lat_2']),
                                    globe=globe),
        
        'aeqd': ccrs.AzimuthalEquidistant(central_longitude=crs_dict['lon_0'], central_latitude=crs_dict['lat_0'],
                                          false_easting = crs_dict['x_0'], false_northing=crs_dict['y_0'],
                                          globe=globe),
        
        
        'eqc': ccrs.PlateCarree(central_longitude=crs_dict['lon_0'], globe=globe),
        'eqdc': ccrs.EquidistantConic(central_longitude=crs_dict['lon_0'], central_latitude=crs_dict['lat_0'],
                                      false_easting = crs_dict['x_0'], false_northing=crs_dict['y_0'],
                                      globe=globe),
        
        'lcc': ccrs.LambertConformal(central_longitude=crs_dict['lon_0'], central_latitude=crs_dict['lat_0'],
                                     false_easting = crs_dict['x_0'], false_northing=crs_dict['y_0'],
                                     standard_parallels=(crs_dict['lat_1'], crs_dict['lat_2']),
                                     globe=None, cutoff=-30),
        'cea': ccrs.LambertCylindrical(central_longitude=crs_dict['lon_0'], globe=globe),
        'merc': ccrs.Mercator(central_longitude=crs_dict['lon_0'],
                              min_latitude=-80, max_latitude=84,
                              globe=globe, latitude_true_scale=None,
                              false_easting = crs_dict['x_0'], false_northing=crs_dict['y_0'],
                              scale_factor=None),
        'longlat': ccrs.PlateCarree(crs_dict.get('lon_0',0), globe)
    }
    if crs_dict['proj'] == 'lcc':
        print('补全cutoff对应项')
    return switch[crs_dict['proj']]






def shp2clip(originfig, ax, gdf, fId=None, region='China'
             #, cover=True, crs=None
             ):
    # 使用 geopandas 读取 shapefile
    # gdf = gpd.read_file(shpfile).to_crs(crs) if crs else gpd.read_file(shpfile)
    
    # 根据区域过滤 GeoDataFrame
    if fId:
        gdf = gdf[gdf[fId] == region]
    
    # 从几何图形创建路径
    vertices = []
    codes = []
    
    for geom in gdf.geometry:
        if geom.type == 'Polygon':
            exterior_coords = geom.exterior.coords
            vertices.extend(exterior_coords)
            codes += [Path.MOVETO] + [Path.LINETO] * (len(exterior_coords) - 2) + [Path.CLOSEPOLY]
        elif geom.type == 'MultiPolygon':
            for polygon in geom.geoms:
                exterior_coords = polygon.exterior.coords
                vertices.extend(exterior_coords)
                codes += [Path.MOVETO] + [Path.LINETO] * (len(exterior_coords) - 2) + [Path.CLOSEPOLY]
    
    # 创建剪切路径
    clip = Path(vertices, codes)
    clip_patch = PathPatch(clip, transform=ax.transData)
    
    # 将剪切路径应用于原始图形的集合
    if hasattr(originfig, 'collections'):
        for contour in originfig.collections:
            contour.set_clip_path(clip_patch)
    else:
        originfig.set_clip_path(clip_patch)
    
    return clip_patch

def set_clip(originfig, ax, clip):
    for contour in originfig.collections:
        contour.set_clip_path(clip)



def readshapefile(shapefile,drawbounds=True,zorder=None,
                      linewidth=0.5,color='k',ax=None,city = None
                      ):
    shf = Reader(shapefile, encoding='utf-8')
    coords = []
    shptype = shf.shapes()[0].shapeType
    for shprec in shf.shapeRecords():
        shp = shprec.shape
        if shptype != shp.shapeType:
            raise ValueError('readshapefile can only handle a single shape type per file')
        if shptype not in [1,3,5,8]:
            raise ValueError('readshapefile can only handle 2D shape types')
        verts = shp.points
        if shptype in [1,8]: # a Point or MultiPoint shape.
            lons, lats = list(zip(*verts))
                # if latitude is slightly greater than 90, truncate to 90
            lats = [max(min(lat, 90.0), -90.0) for lat in lats]
            if len(verts) > 1: # MultiPoint
                x,y = lons, lats
                coords.append(list(zip(x,y)))
            else: # single Point
                x,y = lons[0], lats[0]
                coords.append((x,y))
        else: # a Polyline or Polygon shape.
            parts = shp.parts.tolist()
            for indx1,indx2 in zip(parts,parts[1:]+[len(verts)]):
                lons, lats = list(zip(*verts[indx1:indx2]))
                    # if latitude is slightly greater than 90, truncate to 90
                lats = [max(min(lat, 90.0), -90.0) for lat in lats]
                x, y = lons, lats
                coords.append(list(zip(x,y)))
        # draw shape boundaries for polylines, polygons  using LineCollection.
    if shptype not in [1,8] and drawbounds:
            # get current axes instance (if none specified).
        ax = ax
        lines = LineCollection(coords,antialiaseds=(1,))
        lines.set_color(color)
        lines.set_linewidth(linewidth)
        if zorder is not None:
            lines.set_zorder(zorder)
        ax.add_collection(lines)

        if city != None:
            line = LineCollection(coords[4:5],antialiaseds=(1,))
            line.set_color('r')
            line.set_linewidth(2)
            ax.add_collection(line)





def grid_area(arr_lon, arr_lat, r = 6371000, loc='c'):
    '''
    计算格点面积

    Parameters
    ----------
    arr_lon : array_like
        经度数组
    arr_lat : array_like
        维度数组.
    r : TYPE, optional
        球半径. The default is 6371000.
    loc : TYPE, optional
        坐标位置, 中心, 其他没写, . The default is 'c'.

    Returns
    -------
    arr_s : TYPE
        DESCRIPTION.

    '''
    xs = arr_lon * np.pi/180
    ys = (90 - arr_lat) * np.pi/180  # 从极点开始
    
    x_step = xs[1] - xs[0]
    y_step = ys[1] - ys[0]
    
    
    s = abs(r**2 * x_step * (np.cos(ys-y_step/2) - np.cos(ys+y_step/2)))
    
    arr_s = np.array([s for i in range(len(xs))]).T  # 每个格点的面积
    
    return arr_s













