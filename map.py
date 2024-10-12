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
    
    ax.vlines(x = lon0+length/4, ymin = lat0-size/3*2, ymax = lat0+size/3*2, colors="black", ls="-", lw=lw/2)
    ax.vlines(x = lon0+length/2, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    ax.vlines(x = lon0+length/4*3, ymin = lat0-size/3*2, ymax = lat0+size/3*2, colors="black", ls="-", lw=lw/2)
    ax.vlines(x = lon0+length, ymin = lat0-size, ymax = lat0+size, colors="black", ls="-", lw=lw)
    
    
    fontsize
    
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


























