# -*- coding: utf-8 -*-
"""
Created on Sat 2023/6/19 19:42
@Author : wly
"""

import os, sys, re, time, warnings, inspect, pathlib, math
from functools import partial
from typing import overload
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
import threading
from tqdm import tqdm
from itertools import chain

import pandas as pd
import numpy as np
from alive_progress import alive_bar

import rasterio
import rasterio.mask
from rasterio.windows import Window
from rasterio.warp import calculate_default_transform
from rasterio.enums import Resampling
from rasterio.warp import reproject as _reproject

import mycode.codes as cd
from mycode.decorator import unrepe
from mycode._Class import raster,false



def create_raster(**kwargs):
    memfile = rasterio.MemoryFile()
    return memfile.open(**kwargs)



def get_RasterAttr(raster_in, *args, ds={}, **kwargs):
    """
    获得栅格数据属性

    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        栅格数据或栅格地址
    *args: 所需属性或函数（类中存在的，输入属性名、函数名即可）
    ds: (dict)
        传递操作所需变量,可将全局变量(globals()先赋予一个变量，直接将globals()填入参数可能会报错)输入，
        默认额外可用变量为函数此文件及mycode.code文件的全局变量


    **kwargs: 字典值获得对应属性所需操作，可为表达式，默认参数以字典形式写在“//ks//”之后，在ds中输入相应变量可替代默认参数
            非自身类函数调用时及自身在dic、kwargs中定义的属性调用时，src不可省略。
            必须使用src代表源数据。

            合并属性返回类型为list. e.g.'raster_size': ('height', 'width') -> [900, 600]
            如需特定属性请用函数. e.g. 'raster_size': r"(src.height, src.width)" or r"pd.Serise([src.height, src.width])"
   （dic中有部分，按需求添加，可直接修改dic,效果一致,getattrs中ds参数是为传递操作所需变量,如在dic中添加ds需考虑修改函数参数名及系列变动）

    ---------------------------------
    return:
        args对应属性值列表


    """

    ## 输入变量优先级高
    # now = globals()
    # now.update(ds)
    # ds = now

    # 此文件变量优先级高
    ds.update(globals())
    
    # 定义一些栅格属性
    dic = {'raster_size': r"(src.height, src.width)",
           'cell_size': r"(src.xsize, src.ysize)",
           # 'dtype':r"src.dtypes[0]",
           'bends': 'count', 
           'xsize': r'transform[0]', 
           'ysize': r'abs(src.transform[4])',
           'Bounds': r'[float(f"{i:f}") for i in src.bounds]',
           'values': r'src.read().astype(dtype)//ks//{"dtype":np.float64}',
           'arr': r'src.values.reshape(-1, 1)',
           'df': r'pd.DataFrame(src.values.reshape(-1, 1))',
           # 'shape_b': r"(src.count, src.height, src.width)"
           'shape_b': ('count', 'height', 'width')
           }
    _getattrs = partial(cd.getattrs, **dic)
    
    
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in

    return _getattrs(src, *args, ds=ds, **kwargs)


def add_attrs_raster(src, ds={}, **kwargs):
    """
    向栅格数据中添加属性

    src:栅格数据
    ds:表达式所需变量
    kwargs:属性：对应表达式（"//ks//后为默认参数，在ds中输入相应变量可替代默认参数"）

    """
    dic = {'raster_size': r"(src.height, src.width)",
           'cell_size': r"(src.xsize, src.ysize)",
           'bends': 'count', 
           'xsize': r'transform[0]',
           'ysize': r'abs(src.transform[4])',
           'Bounds': r'[float(f"{i:f}") for i in src.bounds]',
           'values': r'src.read().astype(dtype)//ks//{"dtype":np.float64}',
           'arr': r'src.values.reshape(-1, 1)',
           'df': r'pd.DataFrame(src.values.reshape(-1, 1))',
           #'shape_b': r"(src.count, src.height, src.width)"
           'shape_b': ('count', 'height', 'width')
           }

    dic.update(kwargs)

    data = globals()
    data.update(ds)
    ds = data

    cd.add_attrs(src, run=True, ds=ds, **dic)



def check(src_in=None, dst_in=None,
          src_attrs=None, dst_attrs=None,
          args=None, need=None,
          printf=False, Raise = None,
          w_len=65):
    '''
    检验栅格数据是否统一
    (空间参考、范围、栅格行列数)
    (Bounds为bounds精确到小数点后六位)

    Parameters
    ----------
    输入两栅格
    
    need : 完全自定义比较属性
    args : 添加其他需要比较的属性
    
    src_in : raster
        比较数据之一
    dst_in : raster
        比较数据之一
        
    src_attrs : raster_attrs
        比较的属性集之一
    
    dst_attrs : raster_attrs
        比较的属性集之一
    printf : bool
        是否打印比较对象的不同属性值
    w_len : int
        规范打印的最大宽度
    Raise : class or str
        输入一个错误或警告类。或填入'e'、'w',等于Exception、Warning
        产生一个错误或警告

    Returns
    -------
    judge : bool
        比较的属性是否一致
    diffe : list
        不一致属性的列表
    

    '''
    
    if need:
        attrnames = need
    else:
        args = args or ()
        attrnames = ['crs', 'Bounds', 'raster_size'] + [i for i in args if not(i in ['crs', 'Bounds', 'raster_size'])]
    if src_attrs:
        if "Bounds" in attrnames:
            src_attrs = list(src_attrs) if not isinstance(src_attrs, list) else src_attrs
            for i in range(len(attrnames)):
                if attrnames[i] == "Bounds":
                    src_attrs[i] = [float(f"{n:f}") for n in src_attrs[i]]
    elif src_in:
        src_attrs = get_RasterAttr(src_in, attrnames)

    if dst_attrs:
        if "Bounds" in attrnames:
            dst_attrs = list(dst_attrs) if not isinstance(dst_attrs, list) else dst_attrs
            for i in range(len(attrnames)):
                if attrnames[i] == "Bounds":
                    dst_attrs[i] = [float(f"{n:f}") for n in dst_attrs[i]]
    elif dst_in:
        dst_attrs = get_RasterAttr(dst_in, attrnames)
    else:
        raise Exception('dst_in,dst_attrs必须输入其中一个')
    
    
    diffe = [attrnames[i] for i in range(len(attrnames)) if src_attrs[i] != dst_attrs[i]]
    
    if printf or Raise:
        # 规范打印
        if diffe == []:
            if printf:
                print('栅格属性一致')
            return True, []
        message = '以下属性不一致\n'
        for i in range(len(attrnames)):
            if attrnames[i] in diffe:
                message += (f'\n{"-"*w_len}\
                            \n{("<"+attrnames[i]+">"):-^{w_len}}\
                            \n--->src : {cd.wlen(src_attrs[i],w_len,10)}\
                            \n-\
                            \n--->dst : {cd.wlen(dst_attrs[i],w_len,10)}\n')
                          
        # if message == '以下属性不一致\n':
        #     judge = True if diffe == [] else False
        #     return judge,diffe
        
        if Raise in ('w','e'):
            Raise = Exception if Raise == 'e' else Warning
            
        if Raise is None:
            print(message)
        elif issubclass(Raise, Warning) :
            warnings.warn(message,category=Raise)
        elif issubclass(Raise, Exception):
            raise Raise(message)
        else:
            print(message)
        
            
        
    judge = True if diffe == [] else False
    
    return judge,diffe
    


def check_all(*rasters,args=None, need=None):
    '''
    比较栅格集的属性是否一致
    默认比较是否统一(空间参考、范围、栅格行列数)

    Parameters
    ----------
    *rasters : 
        栅格集
    need : 完全自定义比较属性
    args : 在空间参考、范围、栅格行列数基础上添加其他需要比较的属性
    Returns
    -------
    bool
        返回bool值，表示是否一致

    '''
    # 获得首个栅格元素作为目标值
    dst = cd.get_first(rasters,e_class=str)
    
    def compare(rasters):
        '''将rasters中的每个元素都于首个元素dst比较'''
        if cd.isiterable(rasters) & ~isinstance(rasters, str):
            [compare(x) for x in rasters]
        else:
            if rasters == dst:
                return True
            
            judge,diffe = check(rasters,dst,args=args, need=need)
            if judge:
                return True
            else:
                raise false  # 以false错误退出函数
        # 前面正常运行则全部相等
        return True
            
    try:
        return compare(rasters)
    except false:  # 捕捉false
        return False
    except Exception as e:
        raise e
    



# def checks(*rasters,
#            args=None, need=None,
#            printf=False, Raise = None,
#            w_len=60):
#     if check_all(*rasters,args=None, need=None):
#         return True, []
#     else:
        




def bounds_to_point(left,bottom,right,top):
    return [[left,top],[left,bottom],[right,bottom],[right,top],[left,top]]

def copy_raster(raster_in, out_path):
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    out_ds(ds=src,out_path=out_path)
    


def check_flip(src, n=1):
    bounds = src.bounds
    if bounds[1] > bounds[3]:
        bounds = [bounds[0],bounds[3],bounds[2],bounds[1]]
        src_arr = np.flip(src.read(),axis=1) 
    else:
        src_arr = src.read()
    if n == 1:
        return src_arr
    elif n == 2:
        return src_arr, bounds

   

def _return(out_path=None,get_ds=True,arr=None,profile=None,ds=None):
    '''
    返回函数

    Parameters
    ----------
    输入ds或输入arr和profile
    
    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回重采样后的栅格矩阵（array）和 profile

    '''
    
    if ds:
        ds = rasterio.open(ds) if isinstance(ds, (str,pathlib.Path)) else ds
        profile = ds.profile
        arr = ds.read()
    if not any((profile,arr)):
        raise Exception('请输入ds或输入arr和profile')
    
    if out_path:
        out(out_path=out_path,data=arr, profile=profile)
        
    elif get_ds:
        shape = (profile['count'], profile['height'], profile['width'])
        if arr.shape != shape:
            arr = np.array(arr).reshape(shape)
        ds = create_raster(**profile)
        ds.write(arr)
        return ds
    else:
        return arr,profile




def window(raster_in,
           shape=None, size=None,
           step=None,
           get_dict_id_win=False , get_dict_id_self_win=False,
           get_self_wins=False,
           initial_offset=None,
           Tqbm=False):
    '''
    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        栅格数据或栅格地址
    shape : tuple
          (height,width)
        分割为 height*width个窗口, 未除尽的并入末端窗口
    size : int、float or tuple
          (ysize,xsize)
        窗口的尺寸大小，多余的会生成独立的小窗口不会并入前一个窗口
        
    step : tuple or int
          (ystep,xstep)
        生成滑动窗口
        为滑动步进
        shape、size参数都可以与之配合使用，这里的shape代表了窗口的尺寸为总长、宽除以shape的向下取整。
        e.g.
        src.shape = (20,20)
        shape:(3,3) == size:(6,6)
        末端窗口按正常步进滑动，如有超出会剔除多余部分
        如填int类型，ystep = xstep = step;
        如tuple中存在None,则相应的维度取消滑动，或者说滑动步进等于窗口尺寸。
        e.g.
        3 -> (3,3)
        (3,None) -> (3,xsize)
        (None,3) -> (ysize,3)
    get_self_wins : bool
        如使用滑动窗口是否返回去覆盖后的自身窗口
        
    initial_offset : tuple
                    (initial_offset_x, initial_offset_y)
        初始偏移量,默认为(0,0)

    Returns
    -------
    windows : TYPE
        窗口集
    inxs : TYPE
        对应窗口在栅格中的位置索引

    '''

    assert shape or size, '请填入shape or size'
    assert not (shape and size), 'shape 与 size只填其中一个'

    
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    
    if size:
        if isinstance(size, (int ,float)):
            xsize = size
            ysize = size
        else:
            ysize, xsize = size
        xend = src.width % xsize or xsize
        yend = src.height % ysize or ysize
        
        
        s0 = int(np.ceil(src.height / ysize))
        s1 = int(np.ceil(src.width / xsize))
        shape = (s0, s1)
        
    else:
        xsize, xend0 = divmod(src.width, shape[1])
        ysize, yend0 = divmod(src.height, shape[0])
        xend = xsize + xend0
        yend = ysize + yend0
    
    
    # 生成滑动窗口
    if step:
        
        # 获取x、y 步进
        if isinstance(step, int):
            xstep = step
            ystep = step
        else:
            xstep = step[1] or xsize
            ystep = step[0] or ysize
        # 步进过大，存在缝隙
        if xstep > xsize:
            warnings.warn('步进大于窗口尺寸：xstep > xsize')
        if ystep > ysize:
            warnings.warn('步进大于窗口尺寸：ystep > ysize')
        
        # 计算窗口数
        s00, yend0 = divmod(src.height - ysize, ystep)
        s10, xend0 = divmod(src.width - xsize, xstep)
        
        s0 = int(s00+1 if yend0 == 0 else s00+2)
        s1 = int(s10+1 if yend0 == 0 else s10+2)
        shape = (s0, s1)
        
        # 末端窗口修减
        yend = ysize - (ystep - (yend0 or ystep))
        xend = xsize - (xstep - (xend0 or xstep))

    else:
        # 规范变量
        xstep = None
        ystep = None
    
    initial_offset_x, initial_offset_y = initial_offset or (0,0)  # 初始偏移量
    
    # 返回值变量
    inxs = []  # 窗口位置索引

    windows = []
    if get_self_wins:
        self_windows = []
    

    if Tqbm:
        pbar = tqdm(total=shape[0]*shape[1], desc='生成窗口')

    y_off = initial_offset_y  # y初始坐标
    for y_inx,ax0 in enumerate(range(shape[0])):
        
        x_off = initial_offset_x
        height = yend if ax0 == (shape[0] - 1) else ysize 
        if height == 0:
            continue
        if get_self_wins:
            self_height = yend if ax0 == (shape[0] - 1) else ystep
            
        for x_inx,ax1 in enumerate(range(shape[1])):

            width = xend if ax1 == (shape[1] - 1) else xsize
            if width == 0:
                continue
            if get_self_wins:
                self_width = xend if ax1 == (shape[1] - 1) else xstep
            
            windows.append(Window(x_off, y_off, width, height))
            if get_self_wins:
                self_windows.append(Window(x_off, y_off, self_width, self_height))
            

            inxs.append((y_inx,x_inx))
            
            x_off += xstep or width
            if Tqbm:
                pbar.update(1)

        
        y_off += ystep or height
    if Tqbm:
        pbar.close()

    return (windows, inxs) if not get_self_wins else (windows, inxs, self_windows)






def read(raster_in:raster,
         n=1, tran=True, get_df=True,
         nan=np.nan, dtype=np.float32):
    """
    

    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        栅格数据或栅格地址
    n : 1 or 2 or 3, optional.
        返回几个值. The default is 1.
    tran : bool, optional.
        是否变为单列. The default is True.
    get_df : bool, optional.
        是否变为DataFrame，The default is True.
    nan : optional
        无效值设置.The default is np.nan.
    dtype : 数据类型（class），optional
        矩阵值的格式. The default is np.float64.

    Returns
    -------
    
        栅格矩阵（单列or原型）；profile;shape

    """
    

    assert n in (1,2,3), 'n = 1 or 2 or 3'

    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    arr = src.read().astype(dtype)
    nodata = type(arr[0,0,0])(src.nodata)
    # nodata = dtype(src.nodata)
    shape = arr.shape
    profile = src.profile
    profile.update({'dtype': dtype,
                    'nodata': nan})
    
    # 变形，无效值处理
    df = pd.DataFrame(arr.reshape(-1, 1))
    df.replace(nodata, nan, inplace=True)
    
    # 是否保留变形，是否变为df
    if tran:
        data = df if get_df else np.array(df)

    else:
        data = (pd.DataFrame(np.array(df).reshape(shape)[0]) 
                if (shape[0] == 1) & bool(get_df)
                else np.array(df).reshape(shape))    
    # 返回
    return (data, profile, shape)[:n] if n != 1 else data 



def out(out_path, data, profile):
    """
    
    输出函数，
    可配合形变矩阵
    


    """
    
    shape = (profile['count'], profile['height'], profile['width'])
    
    if data.shape != shape:
        data = np.array(data).reshape(shape)

    with rasterio.open(out_path, 'w', **profile) as src:
        src.write(data)


def out_ds(ds, out_path):
    """
    输出栅格数据

    Parameters
    ----------
    ds : 
        栅格数据
    out_path : str
        输出地址

    Returns
    -------
    无

    """

    arr = ds.read()
    profile = ds.profile
    with rasterio.open(out_path, 'w', **profile) as src:
        src.write(arr)


def renan(raster_in, dst_in=None, nan=np.nan, dtype=np.float32, get_ds=True, out_path=None):
    '''
    替换无效值
    
    dst_in的dtype可能是字符串，不是可调用类对象，如果该类在numpy中没有的话会报错（不知道float对应哪个这里转成np.float64了）
    
    Parameters
    ----------
    raster_in : TYPE
        DESCRIPTION.
    dst_in : TYPE, optional
        DESCRIPTION. The default is None.
    nan : TYPE, optional
        DESCRIPTION. The default is np.nan.
    dtype : TYPE, optional
        DESCRIPTION. The default is np.float32.
    get_ds : TYPE, optional
        DESCRIPTION. The default is True.
    out_path : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    
    # src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    
    
    nan,dtype = get_RasterAttr(dst_in,'nodata','dtype',**{'dtype':r'profile["dtype"]'}) if dst_in else nan,dtype
    # if isinstance(dtype, str):
    #     dtype = dtype if 'np.' in dtype else 'np.' + dtype if dtype != 'float' else 'np.float64'
    #     dtype = eval(dtype)
    arr, profile = read(raster_in=raster_in,n=2,tran=False, get_df=False,nan=nan,dtype=dtype)
    
    return _return(out_path=out_path, get_ds=get_ds, arr=arr, profile=profile)








def merge():...





def resampling(raster_in, out_path =None, get_ds=True,
               re_shape=None, re_scale=None, re_size=None, how='mode', printf=False):
    """
    栅格重采样



    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        输入栅格数据或栅格地址
    out_path : str, optional
        输出地址. The default is None.
    get_ds : TYPE, optional
        返回裁剪后的栅格数据(io.DatasetWriter). The default is True.
    
    
    
    ----------
    重采样类型三选一，都不输入则原样返回
    
    re_shape:形状重采样(tuple)
    (height, width) or (count, height, width)

    re_size:大小重采样(tuple or number)
    (xsize,ysize) or size

    re_scale:倍数重采样(number)
    scale = 目标边长大小/源数据边长大小


    how:(str or int) , optional.
    重采样方式，The default is mode.

    (部分)
    mode:众数，6;
    nearest:临近值，0;
    bilinear:双线性，1;
    cubic_spline:三次卷积，3。
    ...其余见rasterio.enums.Resampling

    printf : 任意值,optional.
        如果发生重采样，则会打印原形状及输入的printf值。The default is False.

    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回重采样后的栅格矩阵（array）和 profile

    """
    if isinstance(raster_in, (list,tuple)):
        
        if out_path is None:
            out_path = [None for i in range(len(raster_in))]
        if len(out_path) != len(raster_in):
            raise Exception('输入栅格与输出路径数量不一致')
        return [resampling(raster_in=_src,out_path=_out_path, get_ds=get_ds,
                           re_shape=re_shape, re_scale=re_scale, re_size=re_size,
                           how=how,printf=printf
                           ) for _src,_out_path in zip(raster_in,out_path)]
    
    def update():  # <<<<<<<<<更新函数
        
        if shape != out_shape:

            if not (printf is False):
                print(f'{printf}的原形状为{shape}')

            transform = rasterio.transform.from_bounds(*bounds, height=out_shape[1], width=out_shape[2])

            profile.data.update({'height': out_shape[1], 'width': out_shape[2], 'transform': transform})
            nonlocal how
            how = how if isinstance(how, int) else getattr(Resampling, how)
            data = src.read(out_shape=out_shape, resampling=how)
        else:
            data = src.read()

        return data

    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    
    # 取出所需参数
    nodata, profile, count, height, width, bounds= get_RasterAttr(src, *(
        'nodata', 'profile', 'count', 'height', 'width', 'bounds'))
    west, south, east, north = bounds
    shape = (count, height, width)

    if re_shape:
        if not(2 <= len(re_shape) <= 3):
            mis = 'resampling:\n当前函数接收re_shape=%s\n请输入二维("height", "width")或三维("count", "height", "width")形状' % str(re_shape)
            raise Exception(mis)
        
        re_shape = list(re_shape)
        re_shape = [count] + re_shape[-2:]

        out_shape = re_shape

        # 更新
        data = update()
        shape = out_shape


    elif re_size:

        if (type(re_size) == int) | (type(re_size) == float):
            xsize = re_size
            ysize = re_size
        else:
            xsize, ysize = re_size
        out_shape = (count, int((north - south) / ysize), int((east - west) / xsize))

        # 更新
        data = update()
        shape = out_shape



    elif re_scale:
        scale = re_scale
        out_shape = (count, int(height / scale), int(width / scale))

        # 更新
        data = update()
        shape = out_shape
    else:
        data = src.read()
        
        
    if out_path:
        with rasterio.open(out_path, 'w', **profile) as ds:
            ds.write(data)
    elif get_ds:
        ds = create_raster(**profile)
        ds.write(data)
        return ds
    else:
        return data, profile



@unrepe(src='raster_in',attrs=['crs'],dst='dst_in',dst_attrs=['crs'],moni_args=('run_how','resolution','shape'),return_and_dict=(_return,{'ds':'raster_in'},{}))
def reproject(raster_in, dst_in=None,
              out_path=None, get_ds=True,
              crs=None,
              how='mode',
              run_how=None,
              resolution=None, shape=(None, None, None)):
    """
    栅格重投影

    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        输入栅格数据或栅格地址
    dst_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py)), optional
        目标投影的栅格数据或栅格地址
    out_path : str, optional
        输出地址. The default is None.
    get_ds : io.DatasetWriter, optional
        返回裁剪后的栅格数据(io.DatasetWriter). The default is True.

    crs : crs.CRS, optional
        目标投影. The default is None.
        
    
    run_how : 
        作用与how相同，但优先级更高，且不会被unrepe装饰器当作重复操作（被unrepe监视，只要不是默认值，函数正常运行）
    how:(str or int) , optional.
    重采样方式，The default is mode.

    (部分)
    mode:众数，6;
    nearest:临近值，0;
    bilinear:双线性，1;
    cubic_spline:三次卷积，3。
    ...其余见rasterio.enums.Resampling
    
    ------------------------------------------------------
    resolution : TYPE, optional
        输出栅格分辨率单位为目标坐标单位. The default is None.
    shape : TYPE, optional
        输出栅格形状. The default is (None, None, None).
        
        ------<resolution与shape不能一起使用>
        
        
   
    Raises
    ------
        dst_in 和 bounds必须输入其中一个
    
    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回重投影后的栅格矩阵（array）和 profile

    """
    # 批量处理，递归
    if isinstance(raster_in, (list,tuple)):
        
        if out_path is None:
            out_path = [None for i in range(len(raster_in))]
        if len(out_path) != len(raster_in):
            raise Exception('输入栅格与输出路径数量不一致')
        return [reproject(raster_in=_src,dst_in=dst_in,
                          out_path=_out_path, get_ds=get_ds,
                          crs=crs,
                          how=how,
                          resolution=resolution, shape=shape) for _src,_out_path in zip(raster_in,out_path)]
    

    # 输入数据整理
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    if crs:
        pass
    elif dst_in:
        crs = get_RasterAttr(dst_in, 'crs')
    else:
        raise Exception("dst_in 和 bounds必须输入其中一个")
    
    # 如果输入栅格与目标投影一致则直接返回
    if src.crs == crs:
        _return(out_path=out_path, get_ds=get_ds, ds=src)
    
    profile = src.profile
    if len(shape) == 2:  # 保证shape是三维的
        shape = [src.count] + list(shape)
    
    
    
    dst_transform, dst_width, dst_height = calculate_default_transform(src.crs, crs, src.width, src.height, *src.bounds,
                                                                       resolution=resolution, dst_width=shape[2],
                                                                       dst_height=shape[1])

    profile.update({'crs': crs, 'transform': dst_transform, 'width': dst_width, 'height': dst_height})
    if run_how:
        how = run_how
    how = how if isinstance(how, int) else getattr(Resampling, how)

    lst = []
    for i in range(1, src.count + 1):
        arrn = src.read(i)
        dst_array = np.empty((dst_height, dst_width), dtype=profile['dtype'])
        _reproject(  
            # 源文件参数
            source=arrn,
            src_crs=src.crs,
            src_nodata=src.nodata,
            src_transform=src.transform,
            # 目标文件参数
            destination=dst_array,
            dst_transform=dst_transform,
            dst_crs=crs,
            dst_nodata=src.nodata,
            # 其它配置
            resampling=how,
            num_threads=2)

        lst.append(dst_array)
    dst_arr = np.array(lst)

    if out_path:
        with rasterio.open(out_path, 'w', **profile) as ds:
            ds.write(dst_arr)
    elif get_ds:
        ds = create_raster(**profile)
        ds.write(dst_arr)
        return ds
    else:
        return dst_arr, profile

def extract(raster_in, dst_in,
            out_path=None, get_ds=True):
    """

    栅格按栅格掩膜提取
    (对掩膜栅格有效值位置栅格值进行提取)


    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        输入栅格数据或栅格地址
    dst_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py)), optional
        掩膜的栅格数据或栅格地址
    out_path : str, optional
        输出地址. The default is None.
    get_ds : bool, optional
        返回提取后的栅格数据(io.DatasetWriter). The default is True.


    Raises
    ------
    Exception
        二者的'crs'、 'raster_size'、 'Bounds'需统一,可先调用unify函数统一栅格数据
        或使用mask函数



    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回提取后的栅格数据(io.DatasetWriter)
    else:返回提取后的栅格矩阵（array）和 profile


    """

    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    dst = rasterio.open(dst_in) if issubclass(type(dst_in), (str,pathlib.PurePath)) else dst_in
    # attrnames = ('crs', 'raster_size', 'Bounds')

    # src_attrs = get_RasterAttr(src, attrnames)
    # dst_attrs = get_RasterAttr(dst, attrnames)
    
    judge,dif = check(src_in=src, dst_in=dst)

    if not judge:
        
        mis = '\nextract 无法正确提取:\n'
        for i in dif:
            mis += f'\n    \"{i}\" 不一致'
        mis += '\n\n----<请统一以上属性>'
        raise Exception(mis)

    # 获得有效值掩膜
    mask_arr = dst.dataset_mask()
    # mask_arr[np.isnan(dst.read(1))] = 0

    if len(mask_arr.shape) == 3:
        mask_arr = mask_arr.max(axis=0)

    mask_arr = np.array([mask_arr for i in range(src.count)])

    # 按掩膜提取
    profile = src.profile
    nodata = src.nodata
    
    # uint格式，None无法输出
    if ('uint' in str(profile['dtype'])) & (nodata == None) :
        profile.update({'dtype':np.float32,'nodata': np.nan})
        nodata = np.nan
    arr = src.read()
    arr = np.where(mask_arr == 0, nodata, arr)

    

    if out_path:
        with rasterio.open(out_path, 'w', **profile) as ds:
            ds.write(arr)
    elif get_ds:
        ds = create_raster(**profile)
        ds.write(arr)
        return ds
    else:
        return arr, profile


@unrepe(src='raster_in',attrs=['Bounds'],dst='dst_in',dst_attrs=['bounds'],moni_kwargs={'Extract':(0,False,None,(),{})},return_and_dict=(_return,{'ds':'raster_in'},{}))
def clip(raster_in,
         dst_in=None, bounds=None,
         inner=False,
         Extract=False, mask=False,
         out_path=None, get_ds=True):
    """
    栅格按范围裁剪
    (须保证投影一致)
    (可按栅格有效值位置掩膜提取)
    
    

    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...)
        输入栅格数据或栅格地址
    dst_in : (str or io.DatasetReader or io.DatasetWriter...), optional
        目标范围的栅格数据或栅格地址
    bounds : tuple, optional
        目标范围(左，下，右，上)
    
    Extract : bool.optional
        调用extract函数
        是否对目标dst_in有效值位置的数据进行提取
        (类似矢量按周长边界裁剪栅格，dst_in必填且为栅格). The default is False.
    
    out_path : str, optional
        输出地址. The default is None.
    get_ds : bool, optional
        返回裁剪后的栅格数据(io.DatasetWriter). The default is True.

    Raises
    ------
       1. dst_in 和 bounds必须输入其中一个
       2. 如使用dst_in, dst_in 和 raster_in空间参考(crs)须一致.
       2. 使用extract，dst_in必填且为栅格
        

    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回裁剪后的栅格矩阵（array）和 profile

    """

    
    # 批量处理，递归
    if isinstance(raster_in, (list,tuple)):
        if out_path is None:
            out_path = [None for i in range(len(raster_in))]
        if len(out_path) != len(raster_in):
            raise Exception('输入栅格与输出路径数量不一致')
        return [clip(raster_in=_src,
                     dst_in=dst_in, bounds=bounds,
                     inner=inner,
                     Extract=Extract, mask=mask,
                     out_path=_out_path, get_ds=get_ds) for _src,_out_path in zip(raster_in,out_path)]
    
 
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in

    if dst_in:

        bounds, crs = get_RasterAttr(dst_in, 'bounds', 'crs')
        if crs != src.crs:
            mis = '\nclip:\n \"crs\"不一致'
            raise Exception(mis)

    elif bounds:
        pass
    else:
        mis = "\nclip:\n\n    \"dst_in\"和\"bounds\"必须输入其中一个"
        raise Exception(mis)
    
    if [float(f"{i:f}") for i in src.bounds] == [float(f"{i:f}") for i in bounds]:
        _return(out_path=out_path, get_ds=get_ds,ds=src)
    
    
    
    
    xsize, ysize, bounds_src, profile, nodata = get_RasterAttr(src, 'xsize', 'ysize', 'bounds', 'profile', 'nodata')
    
    
    # 有些数据集是上下翻转的
    if bounds[1] > bounds[3]:
        bounds = [bounds[0],bounds[3],bounds[2],bounds[1]]
        
        
    if bounds_src[1] > bounds_src[3]:
        bounds_src = [bounds_src[0],bounds_src[3],bounds_src[2],bounds_src[1]]
        src_arr = np.flip(src.read(),axis=1)

    else:
        src_arr = src.read()

    
    # 判断是否有交集
    inter = (max(bounds[0], bounds_src[0]),  # west
             max(bounds[1], bounds_src[1]),  # south
             min(bounds[2], bounds_src[2]),  # east
             min(bounds[3], bounds_src[3]))  # north

    if (inter[2] <= inter[0]) | (inter[3] <= inter[1]):
        # print('输入范围与栅格不重叠')
        if inner:
            Exception('\nclip: 输入范围与栅格不重叠')
        else:
            warnings.warn('\nclip: 输入范围与栅格不重叠')
        
    
    
    # uint格式，None无法输出
    if ('uint' in str(profile['dtype'])) & (nodata == None) :
         profile.update({'dtype':np.float32,'nodata': np.nan})
         nodata = np.nan

    if inner:
        # 取相交范围
        # src_arr = src.read()
        a = int((inter[0] - bounds_src[0]) / xsize)
        b = int((bounds_src[3] - inter[1]) / ysize)
        c = int((inter[2] - bounds_src[0]) / xsize)
        d = int((bounds_src[3] - inter[3]) / ysize)
        
        # dst_arr = src_arr[:, d:b, a:c]

        if mask:
            dst_arr = np.full(src_arr.shape, nodata, object)
            dst_arr[:, d:b, a:c] = src_arr[:, d:b, a:c]
            dst_height = src_arr.shape[1]
            dst_width = src_arr.shape[2]
            dst_bounds = bounds_src
        else:
            dst_arr = src_arr[:, d:b, a:c]
            dst_height = b - d
            dst_width = c - a
            dst_bounds = inter
        
    
    else:
        # 取目标范围
        
        # 填充范围
        # 并集
        union = (min(bounds[0], bounds_src[0]),  # west
                 min(bounds[1], bounds_src[1]),  # south
                 max(bounds[2], bounds_src[2]),  # east
                 max(bounds[3], bounds_src[3]))  # north
    
        union_shape = (src.count, int((union[3] - union[1]) / ysize) + 1, int((union[2] - union[0]) / xsize) + 1)
        union_arr = np.full(union_shape, nodata, object)
    
        # 填入源数据栅格值
        # src_arr = src.read()
    
        a = int((bounds_src[0] - union[0]) / xsize)
        d = int((union[3] - bounds_src[3]) / ysize)
        union_arr[:, d:d + src.height, a:a + src.width] = src_arr
    
        # clip,提取输入范围内的值
        a = int((bounds[0] - union[0]) / xsize)
        b = int((union[3] - bounds[1]) / ysize)
        c = int((bounds[2] - union[0]) / xsize)
        d = int((union[3] - bounds[3]) / ysize)
    

        if mask:
            dst_arr = np.full(union_shape, nodata, object)
            dst_arr[:, d:b, a:c] = union_arr[:, d:b, a:c]
            dst_height = union_arr.shape[1]
            dst_width = union_arr.shape[2]
            dst_bounds = union
        else:
            dst_arr = union_arr[:, d:b, a:c]
            dst_height = b - d
            dst_width = c - a
            dst_bounds = bounds

        
    
    
    dst_transform = rasterio.transform.from_bounds(*dst_bounds, dst_width, dst_height)

    profile.update({'height': dst_height,
                    'width': dst_width,
                    'transform': dst_transform})

    if Extract:
        if dst_in is None:
            raise Exception('\nclip:\n    使用extract，dst_in必填且为栅格')

        # 如果栅格大小不同,重采样
        src_shape = (dst_height, dst_width)
        dst_shape = get_RasterAttr(dst_in, 'raster_size')

        if src_shape != dst_shape:
            dst = resampling(raster_in=dst_in, re_shape=src_shape)
        else:
            dst = dst_in

        ds = create_raster(**profile)
        ds.write(dst_arr)

        return extract(raster_in=ds, dst_in=dst, out_path=out_path, get_ds=get_ds)

    if out_path:
        with rasterio.open(out_path, 'w', **profile) as ds:
            ds.write(dst_arr)
    elif get_ds:
        ds = create_raster(**profile)
        ds.write(dst_arr)
        return ds
    else:
        return dst_arr, profile



def zonal(raster_in, dst_in, stats, areas=None, dic=None, index='area',get_ds=None):
    '''
    分区统计
    栅格统计栅格
    分区栅格应为整型栅格

    Parameters
    ----------
    raster_in : TYPE
        输入栅格
    dst_in : TYPE
        分区数据栅格
    stats : 
       统计类型。基于df.agg(stats) .e.g. 'mean' or ['mean','sum','max']...
    
    areas : 
        需要统计的分区，为None时都统计，默认都统计
    
    dic : dict
        分区数据栅格各值对应属性
    
    index : list,str
    设置表格的索引,e.g. "name"、['name','count']
    如为 None 则为默认索引（0-n）
    默认分区值（如dic中有对应属性则为对应属性值）为索引
    
    get_table、get_ds:
        获得表格、获得栅格数据（DatasetWriter）
        默认只获得表格，可以任意获得
    
    Raises
    ------
    Exception
        二者的'crs'、 'raster_size'、 'Bounds'需统一,可先调用unify函数统一栅格数据
        或使用zonal_u函数

    Returns
    -------
    所需统计值的dataframe，与统计stats对应的栅格数据（数量、意义）

    '''
    


    
    assert isinstance(stats, (list,tuple)) , '请保证stats是一个list或tuple'
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    dst = rasterio.open(dst_in) if issubclass(type(dst_in), (str,pathlib.PurePath)) else dst_in
    
    
    judge,dif = check(src_in=src, dst_in=dst)

    if not judge:
        
        mis = '\nextract 无法正确提取:\n'
        for i in dif:
            mis += f'\n    \"{i}\" 不一致'
        mis += '\n\n----<请统一以上属性>'
        raise Exception(mis)
    
    # stats = [stats] if isinstance(stats, str) else stats
    
    
    df_src = read(raster_in=src, n=1)
    df_dst = read(raster_in=dst, n=1)
    
    
    df_return = pd.DataFrame()
    
    areas = areas or list(df_dst[0].unique())
    
    if len(areas) >= 1000:
        warnings.warn('\n分区数为%d,分区栅格可能为浮点型栅格'%len(areas))

    
    dic = dic or {}
    
    for area in areas:

        # virtual = df_src[df_dst[0].isin([area])]  # isin()解决np.nan不被 == 检索问题 ,但慢很多还是改用了条件判断
        if area == None:
            virtual = df_src[df_dst==area]
        elif np.isnan(area):  # 不支持None,所以分了三段
            virtual = df_src[df_dst[0].isna()]
        else:
            virtual = df_src[df_dst==area]
            
        stats_values = virtual.agg(stats,axis=0)
        stats_values.columns = [area]
        df_return = pd.concat([df_return,stats_values],axis=1)
    

    df_return = df_return.T
    if len(df_return.columns) == 1:
        stat_names = [stat if isinstance(stat, str) else stat.__name__ for stat in stats]
        df_return.loc[:,stat_names] = np.nan
    # df_return.set_index('area',inplace=True)
    
    results = []
    
    
    
    if get_ds:
        profile = src.profile
        profile['nodata'] = np.nan
        get_ds = get_ds if isinstance(get_ds, (list,tuple)) else list(df_return.columns)
        shape = (profile['count'], profile['height'], profile['width'])
        for idx in get_ds:
            df_ds = df_src*np.nan  # 初始化等长df
            dfn = df_return[idx]
            for i in areas:
                df_ds[df_dst[0] == i] = dfn.loc[i]
            arr = np.array(df_ds).reshape(shape)
            ds = create_raster(**profile)
            ds.write(arr)
            results.append(ds)
    

    df_return.reset_index().rename(columns={"index":"area"})
    
    if index:
        df_return.set_index(keys=index,drop=True,inplace=True)
    
    results.insert(0, df_return)
    

    return results if len(results) != 1 else results[0]
            


def three_sigma(raster_in,dst_in=None,out_path=None, get_ds=True):
    '''
    三倍标准差剔除离散值

    Parameters
    ----------
    raster_in : TYPE
        DESCRIPTION.
    dst_in : TYPE
        DESCRIPTION.
    out_path : TYPE, optional
        DESCRIPTION. The default is None.
    get_ds : TYPE, optional
        DESCRIPTION. The default is True.

    Raises
    ------
    Exception
        DESCRIPTION.

    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回重投影后的栅格矩阵（array）和 profile

    '''
    
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    
    if dst_in is None:
        df_src,profile = read(src,2)
        df_src = cd.three_sigma(df_src)
    
    else:
        dst = rasterio.open(dst_in) if issubclass(type(dst_in), (str,pathlib.PurePath)) else dst_in
        
        
        judge,dif = check(src_in=src, dst_in=dst)
    
        if not judge:
            
            mis = '\nextract 无法正确提取:\n'
            for i in dif:
                mis += f'\n    \"{i}\" 不一致'
            mis += '\n\n----<请统一以上属性>'
            raise Exception(mis)

        
        df_src,profile = read(src,2)
        df_dst = read(dst)
        
        areas = list(df_dst[0].unique())
        if len(areas) >= 1000:
            warnings.warn('\n分区数为%d,分区栅格可能为浮点型栅格'%len(areas))
        
        for area in areas:
            # areax = df_dst[(df_dst==area)]
            areax = (df_dst==area)
            df_src = cd.three_sigma(df_src,[areax])
            
            
            
            # df_x = df_src[df_dst==area]
            # mean = df_x[0].mean()
            # std = df_x[0].std()
            
            # df_src[(df_x[0] < mean - 3 * std) | (df_x[0] > mean + 3 * std)] = np.nan
    
    return _return(out_path, get_ds, arr=df_src, profile=profile)


@unrepe(src='raster_in',attrs=['crs','Bounds','raster_size'],dst='dst_in',moni_args=['run_how'],moni_kwargs={'Extract':(0,False,None,(),{},'')},return_and_dict=(_return,{'ds':'raster_in'},{}))
def unify(raster_in, dst_in,
          out_path=None, get_ds=True,
          Extract=False, how='mode',run_how=None,
          **kwargs):
    """
    统一栅格数据
    (空间参考、范围、行列数)
    
    范围的误差在小数点后9位左右(绝大多数时候用bounds也不会报错)，
    因此检查统一函数check比较的范围Bounds为bounds精确到小数点后六位。
    如有问题可用check中printf参数查看

    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        输入栅格数据或栅格地址
    dst_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py)), optional
        目标投影的栅格数据或栅格地址
    out_path : str, optional
        输出地址. The default is None.
    get_ds : io.DatasetWriter, optional
        返回统一后的栅格数据(io.DatasetWriter). The default is True.
    Extract : bool, optional
        是否按有效值位置提取. The default is False
    
    run_how : 
        作用与how相同，但优先级更高，且不会被unrepe装饰器当作重复操作（被unrepe监视，只要不是默认值，函数正常运行）
    how:(str or int) , optional.
    重采样方式，The default is mode.

    (部分)
    mode:众数，6;
    nearest:临近值，0;
    bilinear:双线性，1;
    cubic_spline:三次卷积，3。
    ...其余见rasterio.enums.Resampling
    


    **kwargs:
        接收调用函数(reproject、clip、resampling)的其他参数.
        e.g. printf(resampling中：如果发生重采样，则会打印原形状及printf值。The default is False.)

    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回重采样后的栅格矩阵（array）和 profile

    """
    
    
    
    # 是否按有效值位置提取
    if Extract:
        ds = unify(raster_in=raster_in, dst_in=dst_in, how=how, Extract=False, out_path=None, get_ds=True, **kwargs)
        kwargs_extract = {}  # 设置默认参数
        kwargs_extract.update({k: v for k, v in kwargs.items() if k in inspect.getfullargspec(extract)[0]}) #接收其他参数 
        
        return extract(raster_in=ds, dst_in=dst_in,out_path=out_path,get_ds=get_ds,**kwargs_extract)

    # 获得栅格变量
    src = rasterio.open(raster_in) if issubclass(type(raster_in), (str,pathlib.PurePath)) else raster_in
    dst = rasterio.open(dst_in) if issubclass(type(dst_in), (str,pathlib.PurePath)) else dst_in
    

    # 检查哪些属性需要统一
    judge,dif = check(src_in=src, dst_in=dst)
    if judge:
        return _return(out_path=out_path,get_ds=get_ds,ds=src)
    elif 'crs' in dif:
        run = 3
    elif 'Bounds' in dif:
        run = 2
    elif 'raster_size' in dif:
        run = 1
    else:
        raise Exception('有问题')
        

    
    shape = dst.shape
    
    
    ds = raster_in
    # 重投影（空间参考）
    if run == 3:
        kwargs_reproject = {}  # 设置默认参数
        kwargs_reproject.update({k: v for k, v in kwargs.items()
                                 if k in inspect.getfullargspec(reproject)[0] + inspect.getfullargspec(reproject)[4]})  #接收其他参数 
        ds = reproject(raster_in=ds, dst_in=dst, how=how, **kwargs_reproject)
    # 裁剪（范围）
    
    if run >= 2:
        kwargs_clip = {}  # 设置默认参数
        kwargs_clip.update({k: v for k, v in kwargs.items()
                            if k in inspect.getfullargspec(clip)[0] + inspect.getfullargspec(clip)[4]}) #接收其他参数 
        ds = clip(raster_in=ds, dst_in=dst,**kwargs_clip)
    # 重采样（行列数）
    if ds.shape[-2:] == dst.shape[-2:]:
        return _return(out_path=out_path, get_ds=get_ds, ds=ds)
    kwargs_resapilg = {}  # 设置默认参数
    kwargs_resapilg.update({k: v for k, v in kwargs.items()
                            if k in inspect.getfullargspec(resampling)[0] + inspect.getfullargspec(resampling)[4]})  #接收其他参数 
    return resampling(raster_in=ds, out_path=out_path,how=how, get_ds=get_ds, re_shape=shape, re_size=None, re_scale=None, **kwargs_resapilg)



def unify_wins(raster_in, dst_in,
              out_path=None, get_ds=True,
              Extract=False, how='mode',run_how=None,
              **kwargs):
    pass




"""
以下函数包含统一空间参考

如须多次使用同一目标栅格dst_in，建议先手动使用reproject统一，减少reproject函数的调用
手动统一后可以不去寻找原函数，函数会跳过以统一栅格


"""



def clip_u(raster_in,
           dst_in=None,bounds=None,
           inner=False,
           Extract=False,mask=False,
           out_path=None, get_ds=True,**kwargs):
    '''
    栅格裁剪
    按范围裁剪。
    可提取。
    含临时统一投影操作。
    

    Parameters
    ----------
    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
       输入栅格数据或栅格地址
    dst_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py)), optional
       目标范围的栅格数据或栅格地址
    bounds : tuple, optional
       目标范围(左，下，右，上)
      
    inner : 是否取交集，默认False
    
    Extract : bool.optional
       调用extract函数
       是否对原栅格处于掩膜栅格有效值位置的值进行提取
       (类似矢量按周长边界裁剪栅格，dst_in必填且为栅格). The default is False.
    
    mask : 是否保留并集
    
    out_path : str, optional
       输出地址. The default is None.
    get_ds : bool, optional
       返回裁剪后的栅格数据(io.DatasetWriter). The default is True.
      
    Raises
    ------
       1. "dst_in"和"bounds"必须输入其中一个
       2. 使用extract，dst_in必填且为栅格
       
       
    Returns
    -------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回栅格数据(io.DatasetWriter)
    else:返回裁剪后的栅格矩阵（array）和 profile
    



    '''


    # 按范围裁剪，无须统一
    if bounds:
        return clip(raster_in=raster_in, bounds=bounds, out_path=out_path, get_ds=get_ds,mask=mask, inner=inner)
    
    # 检查参数
    if not dst_in:
        excs = "\nclip:\n\n    \"dst_in\"和\"bounds\"必须输入其中一个"
        raise Exception(excs)
    
    # 保证空间参考统一
    src_crs = get_RasterAttr(raster_in,'crs')
    dst_crs = get_RasterAttr(dst_in,'crs')
    
    if src_crs != dst_crs:
        ds = reproject(dst_in,raster_in)
    else:
        ds = dst_in
    
    # 调用clip函数
    return clip(raster_in=raster_in, dst_in=ds,inner=inner,mask=mask, Extract=Extract, out_path=out_path, get_ds=get_ds) 




def mask(raster_in,
         dst_in=None,bounds=None,
         Extract=False,Clip=True,
         out_path=None, get_ds=True,**kwargs):
    """
    栅格按栅格掩膜提取,
    对原栅格处于掩膜栅格有效值位置的值进行提取，也可对范围提取
    支持不同空间参考
    

    --------------------------

    raster_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py))
        输入栅格数据或栅格地址
        
    dst_in : (str or io.DatasetReader or io.DatasetWriter...(in io.py)), optional
        掩膜的栅格数据或栅格地址
    bounds : tuple, optional
        目标范围(左，下，右，上),bounds与dst_in填其中一个，bounds优先级更高
    
    
    Extract : bool.optional
        调用extract函数
        是否对目标dst_in有效值位置的数据进行提取
        (类似矢量按周长边界裁剪栅格，dst_in必填且为栅格). The default is False.
        
    Clip : bool,optional
        是否裁剪. The default is True.
    out_path : str, optional
        输出地址. The default is None.
    get_ds : bool, optional
        返回提取后的栅格数据(io.DatasetWriter). The default is True.

    
    Raises
    ------
       1. "dst_in"和"bounds"必须输入其中一个
       2. 使用extract，dst_in必填且为栅格
       3. 须保证范围与输入栅格有重叠
      
       
    Returns
    ------------------
    if out_path:生成栅格文件，不返回
    elif get_ds:返回提取后栅格数据(io.DatasetWriter)
    else:返回提取后的栅格矩阵（array）和 profile

    """
    

    
    return clip_u(raster_in=raster_in,
                  dst_in=dst_in,bounds=bounds,
                  inner=True,
                  Extract=Extract,mask=not(Clip),
                  out_path=out_path, get_ds=get_ds,**kwargs)

       
"""
以下函数内部调用unify统一函数，支持不同空间参考、范围、行列数栅格之间的操作
不更改原栅格，将目标栅格向原栅格转换，以下函数都是如此

如须多次使用同一目标栅格dst_in，建议先手动使用unify统一，减少unify函数的调用，
手动统一后可以不去寻找原函数，函数会跳过以统一栅格


"""

def zonal_u(raster_in, dst_in, stats, areas=[], dic=None, index='area',get_ds=None,**kwargs):
    '''
    分区统计
    含临时统一操作
    分区栅格应为整型栅格
    
    Parameters
    ----------
    raster_in : TYPE
        输入栅格
    dst_in : TYPE
        分区数据栅格
    stats : list or tuple
       统计类型。基于df.agg(stats). e.g. ['mean'] or ['mean','sum','max']...
    
    dic : dict
        分区数据栅格各值对应属性，默认为值本身
    **kwargs : TYPE
       unify可填入的其他参数

    Returns
    -------
    dataframe
        所需统计值的dataframe

    '''
    
    ds = unify(raster_in = dst_in, dst_in = raster_in, out_path=None,get_ds=True, **kwargs)
    return zonal(raster_in=raster_in,dst_in=ds, stats=stats,area=areas,dic=dic,index=index,get_ds=get_ds)
       
 


# src = raster_in if type(raster_in) in (i[1] for i in inspect.getmembers(rasterio.io)) else rasterio.open(raster_in)
# dst = dst_in if type(dst_in) in (i[1] for i in inspect.getmembers(rasterio.io)) else rasterio.open(dst_in)







if __name__ == '__main__':
    # sys.exit(0)
    raster_in = r'F:/PyCharm/pythonProject1/arcmap/015温度/土地利用/landuse_4y/1990-5km-tiff.tif'

    dst_in = r'F:\PyCharm\pythonProject1\arcmap\007那曲市\data\eva平均\eva_2.tif'

    out_path = r'F:\PyCharm\pythonProject1\代码\mycode\测试文件\eva5_1.tif'
    
    out_path1 = r'F:\PyCharm\pythonProject1\arcmap\015温度\zonal\grand_average.xlsx'


    # x = check_all(raster_in,raster_in,dst_in)
    src = rasterio.open(raster_in)
    windows, ids, self_windows = window(r'F:\PyCharm\pythonProject1\代码\008并行分窗口\20230819\lst2000\LSTD1_2000.tif',
                                        size=200,step=1,get_self_wins=True,Tqbm=1)
    # windows1, ids1 = window(src,size=200,step=None)
    # os.chdir(r'F:/Python/pythonlx/9 tif_mean')
    # x = rasterio.band(src,1)
    # pro = src.profile
    # src.checksum(1)
    # src.lnglat()
    # src.files
    # src.overviews(1)
    # src.window_bounds()
    # src.write_transform()
    # # src.
    # nodata = src.nodata
    
    # arr = src.read()
    
    # arr == nodata
    # pro['dtype'] = 'float32'
    
    # ds = create_raster(**pro)
    
    
    # ds.profile['dtype']
    
    # ds.close()
    
    # dst = rasterio.open(r'F:\PyCharm\pythonProject1\代码\mycode\测试文件\float2.tif','w',**pro)
    # ds = renan(src)
    
    # arr = ds.read()
    
    # dst.profile
    
    
    
    
    
    # check(raster_in,dst_in=dst_in,printf=1,w_len=80)
    # df = zonal_u(raster_in=dst_in, dst_in=raster_in, stats = ['sum','max','min'])
    # src.dtypes
    # dst = unify(raster_in,dst_in)
    # ds = three_sigma(dst_in,dst)
    # out_ds(ds, out_path)
    
    
    # ws = src.read()
    # w = src.block_window(1,0,0)
    
    # list(ws)
    
    # # src.block_shapes = [(1368/2,1728/2)]
    
    # from sys import getsizeof as getsize
    # var = object()
    # print(getsize(ws))
    
    
    # s = time.time()
    # ds = unify(raster_in,dst_in=dst_in)
    # print('运行时间：%.2f'%(time.time()-s)+'s')
    # s = time.time()
    # ds1 = unify(dst_in,dst_in=ds)
    # ds1 = unify(dst_in,dst_in=ds)
    # ds1 = unify(dst_in,dst_in=ds)
    # ds1 = unify(dst_in,dst_in=ds)
    # ds1 = unify(dst_in,dst_in=ds)
    # ds1 = unify(dst_in,dst_in=ds)
    # print('运行时间：%.2f'%(time.time()-s)+'s')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    






































    





















