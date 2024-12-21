# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 10:39:24 2024

@author: wly
"""

from .reproject import reproject





def resampling(raster_in, out_path=None, get_ds=True,
               dst_resolution=None, dst_shape=None,
               how='nearest', nodata=None,
               num_threads=4, 
               **creation_options):
    '''
    

    Parameters
    ----------
    raster_in : 地址或栅格类
        输入栅格
    dst_in : 地址或栅格类, optional
        目标栅格
    out_path : str, optional
        输出地址.
        Default: None.
    get_ds : bool, optional
        是否输出临时栅格.当out_path不为None时并不会输出. Default: True.
    crs : CRS or str, optional
        目标投影, None且dst_in=None则与输入栅格相同，不与dst_in同时使用. Default: None.
    how: (str or int) , optional.
        重采样方式，Default: nearest.

        (部分)\n
        mode:众数，6;\n
        nearest:临近值，0;\n
        bilinear:双线性，1;\n
        cubic_spline:三次卷积，3。\n
        ...其余见rasterio.enums.Resampling
    
    
    nodata : 数字类, optional
        目标无效值，默认与输入栅格相同(if set), 或者0(GDAL default) . Default: None.
    dst_resolution: tuple (x resolution, y resolution) or float, optional
        目标分辨率，以目标坐标参考为单位系统.不能与dst_shape一起使用
        
    dst_shape : (dst_height, dst_width) or (count, dst_height, dst_width) tuple or list, optional
        目标行列数。不能与dst_resolution一起使用.
    num_threads : int, optional
        线程数 . Default: 4.
    '''
    # 参数检查
    if dst_shape and dst_resolution:
        raise ValueError("dst_shape和dst_resolution不能一起使用。")
    
    if (dst_shape is None) and (dst_resolution is None):
        raise ValueError("dst_shape和dst_resolution请输入其一。")
    
    # 行列数设置
    if dst_resolution is not None:
        dst_height, dst_width = (None, None)
    elif dst_shape is not None:
        length = len(dst_shape)
        if length == 3:
            dst_height, dst_width = dst_shape[1:]
        elif length == 2:
            dst_height, dst_width  = dst_shape
        else:
            raise ValueError('dst_shape长度错误(%d)，请输入(dst_height, dst_width) 或 (count, dst_height, dst_width)'%length)
        
    # 调用函数
    return reproject(raster_in,
                     dst_in=None,crs=None, # 关闭重投影
                     out_path=out_path, get_ds=get_ds,
                     how=how, dst_nodata=nodata,
                     resolution=dst_resolution, dst_width=dst_width, dst_height=dst_height,
                     num_threads=num_threads,
                     **creation_options)
    
    













