# -*- coding: utf-8 -*-
"""
Created on Mon May  8 20:26:45 2023

@author: wly
"""

import os
import numpy as np
import pandas as pd
import sys
import warnings
import traceback
import datetime
from typing import overload, Sequence, Iterator
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from functools import partial,wraps
from sys import getsizeof as getsize


def recombination_df(ls_df, ls_name=None):
    '''
    按列名重组df,相同的列合并为新的df

    Parameters
    ----------
    ls_df : TYPE
        df列表
    ls_name : TYPE
        新列名，与df列表对应, 默认则从0开始

    Returns
    -------
    dic_df : dict
        原列名为key，新生成的df为值

    '''
    if ls_name is None:
        ls = []
    ls_name += list(range(len(ls_df) - len(ls_name)))
    ls = []
    for dfn, name in zip(ls_df,ls_name):
        dfn = dfn.stack()
        dfn.name = name
        ls.append(dfn)
    df_all = pd.concat(ls,axis=1).stack().unstack(1)
    
    
    dic_df = {}
    for v in df_all.columns:
        dfn = df_all[v]
        dfn = dfn.unstack()
        dic_df[v] = dfn
    return dic_df



def wlen(x,n:int,f_len:int=0,f_str:str =None):
    '''
    重组字符串，规定每行的最大长度

    Parameters
    ----------
    x : TYPE
        输入的字符串，或想打印的变量
    n : int
        行的限定长度
    f_len : (str,int), optional
        第一行预留的长度，如第一行有说明文字可用此参数.
        The default is 0.
    f_str : str, optional
        要在第一行添加的字符串说明输出会加上，填了f_str就不用填f_len

    Raises
    ------

    Returns
    -------
    new_x : str
        重组后字符串

    '''
    # 字符串初始化
    x = str(x) if not isinstance(x, str) else x
    x = (f_str if f_str else '-'*f_len) + x.replace('\n', '')  # 添加头文字，消除换行符

    # 处理
    hlen = len(x) // n + 1
    # lst = [x[n*i:n*(i+1)] for i in range(hlen)]
    new_x = '\n'.join([x[n*i:n*(i+1)] for i in range(hlen)])
    
    return new_x if f_str else new_x[f_len:]

def df_split(df,column,sep,dtype=None):
    columns = df.columns
    
    
    df2 = df[column].str.split(sep, expand=True).stack().reset_index(level=1, drop=True).rename(column)
    df1 = df.drop(column, axis=1)
    df = df1.join(df2) if len(df1.index) != len(df2.index) else df
    if dtype:
        df[column] = df[column].astype(dtype)
    return df.loc[:,columns]
    
    
    

def tranf_value_index_col(df, tranf=None, col_name=None, index_name=None, split_multi=True,clear=True):
    
    '''
    dataframe以值显示索引与列
    '''
    
    # def clear(x):
        
    #     if x == 0:
    #         return True
    #     else:
    #         return bool(x)
    
    num_row, num_col = df.shape
    arr = df.values.reshape(-1)
    column = list(df.columns)*num_row
    index = [i for i in list(df.index) for n in range(num_col)]
    
    col_name = col_name or 'column'
    index_name = index_name or 'index'

    if tranf == 'index':
        df_tranf = pd.DataFrame({index_name : index},index=arr)
    elif tranf == 'column':
        df_tranf = pd.DataFrame({col_name : column},index=arr)
    else:
        df_tranf = pd.DataFrame({index_name : index, col_name : column},index=arr)
    
    return df_tranf



def binary_conversion(var: int):
    """
    二进制单位转换
    :param var: 需要计算的变量，bytes值
    :return: 单位转换后的变量，kb 或 mb
    """
    # assert isinstance(var, int)
    if var <= 1024:
        return f'占用 {round(var / 1024, 2)} KB内存'
    else:
        return f'占用 {round(var / (1024 ** 2), 2)} MB内存'

def size(x):
    return binary_conversion(getsize(x))




def filename(path):
    return os.path.basename(path).split('.')[0]



def Hex_to_RGB(hex):
    r = int(hex[1:3],16)
    g = int(hex[3:5],16)
    b = int(hex[5:7], 16)
    rgb = str(r)+' '+str(g)+' '+str(b)
    print(rgb)
    return rgb

def filtration(x, a, b):
    return max(a, min(x, b))

def three_sigma(array,areas=None) -> np.array:
    '''
    三倍标准差剔除离散值

    Parameters
    ----------
    array : array_like
        可正常转为数组的元素
        需要操作的数组
    areas : TYPE, optional
        分区数组列表，每个元素需于数组形状相同，
        每个元素中的有效值（None、np.nan、False为无效值）为一个区域.
        （如不同的时间或地区分区剔除，不受其他区域影响）
        None则不分区，（默认值）
        The default is None.

    Returns
    -------
    arr : np.array
        剔除离散值后的数组

    '''
    
    arr = np.array(array).astype('float64')
    
    if areas is None:
        mean = np.nanmean(arr)
        std = np.nanstd(arr)
        arr[(arr < mean - 3 * std) | (arr > mean + 3 * std)] = np.nan
        
    else:
        for area in areas:

            warnings.filterwarnings('ignore',category=RuntimeWarning)
            area = np.array(area)
            arrx = np.where((np.isnan(area)|(area==False)|(area==None)),np.nan,arr)
            mean = np.nanmean(arrx)
            std = np.nanstd(arrx)
            arr[(arrx < mean - 3 * std) | (arrx > mean + 3 * std)] = np.nan
        warnings.filterwarnings('default')

    return arr




def interval(array, Min=0, Max=1, nodata=np.nan, dtype='float64', drop=True):
    arr = np.array(array).astype(dtype)
    
    min_value = np.quantile(arr, Min)
    max_value = np.quantile(arr, Max)
    
    if drop:
        arr[(arr < min_value) | (arr > max_value)] = nodata
    else:
        arr[(arr < min_value)] = min_value
        arr[(arr > max_value)] = max_value
    
    return arr
    
    


class TempDir:
    """Context manager to temporarily change the current working directory."""
    
    def __init__(self, new_dir):
        self.new_dir = new_dir
        self.old_dir = None

    def __enter__(self):
        # Store the old directory and change to the new one
        self.old_dir = os.getcwd()
        os.chdir(self.new_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Change back to the old directory, ignoring any exceptions
        os.chdir(self.old_dir)




def zonal(src_in, dst_in, stats, areas=None, dic=None,index=['name']):
    '''
    矩阵分区统计
    

    Parameters
    ----------
    raster_in : TYPE
        输入栅格
    dst_in : TYPE
        分区数据栅格
    stats : list or tuple
       统计类型。基于df.agg(stats) .e.g. 'mean' or ['mean','sum','max']...
    areas : list or tuple
        需要统计的分区，为None时都统计，默认都统计
    dic : dict
        分区数据栅格各值对应属性
    
    index : list,str
    设置表格的索引,e.g. "name"、['name','count']
    如为 None 则为默认索引（0-n）
    默认分区值（如dic中有对应属性则为对应属性值）为索引
    

    
    Raises
    ------
    Exception
        二者的shape需一致
        

    Returns
    -------
    所需统计值的dataframe

    '''
    
    def agg(area):
        serice = pd.Series({'name':dic.get(area,area)})
        virtual = df_src[df_dst[0].isin([area])]  # isin()解决np.nan不被 == 检索问题
        value = virtual.agg(stats,axis=0)
        serice = pd.concat([serice,value])
        return serice
    
    
    assert isinstance(stats, (list,tuple)) , '请保证stats是一个list或tuple'
    src = np.array(src_in)
    dst = np.array(dst_in)
    
    assert src.shape == dst.shape ,'输入矩阵与分区矩阵形状不同\narr_in:%s\ndst_in:%s'%(src.shape, dst.shape)
    
    
    
    # stats = [stats] if isinstance(stats, (str)) else stats
    
    
    
    df_src = pd.DataFrame(src.reshape((-1,1)))
    df_dst = pd.DataFrame(dst.reshape((-1,1)))
    
    
    unique = list(df_dst[0].unique())
    areas = areas or unique
    
    if len(areas) >= 1000:
        warnings.warn('\n分区数为%d,分区数据可能为连续数据'%len(areas))
    
    
    dic = dic or {}
    # df_return = pd.DataFrame(index=(['name']+stats))
    # df_return = pd.DataFrame()
    
    ## 多线程 ,thread_count=None,如果使用加上这个参数，换掉下面的循环，不过数据量要很大才会有明显效果，我4000*4000的矩阵，8个分区，好像都影响不大
    ## thread_count = None
    # pool = ThreadPoolExecutor(thread_count)
    # pl_rst = pool.map(agg, areas) # 多线程
    # # pl_rst = [agg(area) for area in areas] # 循环
    # df_return = pd.concat(pl_rst,axis=1)
    
    #循环
    ls_serice = []
    
    for area in areas :
        
        serice = pd.Series({'name':dic.get(area,area)})
        if area in unique:
            # virtual = df_src[df_dst[0].isin([area])]  # isin()解决np.nan不被 == 检索问题,但慢很多还是改用了条件判断
            if area == None:
                virtual = df_src[df_dst==area]
            elif np.isnan(area):
                virtual = df_src[df_dst[0].isna()]
            else:
                virtual = df_src[df_dst==area]
            value = virtual.agg(stats,axis=0)
            serice = pd.concat([serice,value])
        ls_serice.append(serice)
    df_return = pd.concat(ls_serice,axis=1).T
    #

    if len(df_return.columns) == 1:
        stat_names = [stat if isinstance(stat, str) else stat.__name__ for stat in stats]
        df_return.loc[:,stat_names] = np.nan
    if index is None:
        df_return.reset_index(drop=True,inplace=True)
    else:
        df_return.set_index(keys=index,drop=True,inplace=True)
    
    return df_return
    
    
    
def count(arr):
    arr = np.array(arr)
    
    x= arr[~np.isnan(arr)]
    
    return len(x)
    
    
    


# nnan = []
def get_num(x,lst_and = []):   
    x = str(x) + '/'
    est = 'f'
    nums = []
    global nnan
    
    ls = [str(i) for i in range(10)] + lst_and
    for i in range(len(x)):
        n = x[i]
        if est == 'y':
            if not n in ls:
                end = i
                num = x[start:end]
                nums.append(num)
                est = 'f' 
                if not n in nnan:
                    nnan.append(n)
        elif n in ls:
            start = i
            est = 'y'           
        else:
            if not n in nnan:
                nnan.append(n)
            
    if len(nums) < 3:
        for i in range(3 - len(nums)):
            nums.append(0)
    return pd.Series(nums,index=range(1,len(nums)+1))





# -----------------------------------------------------------------------------------------



def isiterable(x):
    
    '''
    判断x能否迭代
    
    返回 bool类型
    '''
    try:
        iter(x)
        return True
    except:
        return False




def get_first(iterable,i_class=None,e_class=None):
    '''
    获取嵌套可迭代对象中的第一个元素

    Parameters
    ----------
    iterable : TYPE
        可迭代对象.
    
    i_class : list, optional
        使用的可迭代类型。
        如果获取的元素是这个类型则会继续递归，直到检索到非i_class的元素才会返回。
        默认使用所有可迭代类型。 The default is None.
    
    
    e_class : list, optional
        排除的可迭代类型。
        如果检索到元素是这些类型不会继续递归，而是返回这个元素.如str有时需被排除
        The default is None.

    Returns
    -------
    TYPE
        第一个元素

    '''
    # 判断是否可迭代并将zip对象转tuple
    if isiterable(iterable):
        if isinstance(iterable, zip):
            iterable = tuple(iterable)
    else:
        raise TypeError('iterable不可迭代')
        # return iterable  # 返回自身
    
    # 判断是否是使用的可迭代类型，是否是排除的可迭代类型
    if i_class:
        include = isinstance(iterable[0], i_class)
    else:
        include = isiterable(iterable[0])
    if e_class:
        exclude = isinstance(iterable[0],e_class)
    else:
        exclude = False
    
    # 即是include又不是exclue则继续运行，否则返回第一个元素
    if include & (not exclude):
        if iterable == iterable[0]:  # str的返回方式
            return iterable
        else:
            return get_first(iterable[0])
    else:
        return iterable[0]  # 返回第一个元素




def evals(*runs,**kwargs):
    '''
    批量操作函数

    Parameters
    ----------
    *runs : TYPE
        操作字符串集
    **kwargs : TYPE
        额外可用变量，默认可用此文件全局变量

    Returns
    -------
    returns : 
        结果列表,如果列表只有一个元素，则直接返回这个元素

    '''
    
    results = []
    for run in runs:

        if isiterable(run) & (type(run) != str):
            # 递归
            results.append([evals(i,**kwargs) for i in run])
        else:
            # # 解包变量
            # for k,v in kwargs.items():
            #     locals()[k] = v

            # 操作
            results.append(eval(run,globals(),kwargs))
            # results.append(eval(_run))

    return results[0] if len(results) == 1 else results

def getattrs(src, *args, ds={}, get_runs=False, **kwargs):
    '''
    批量获得类属性

    Parameters
    ----------
    src : class
        被查询的类.
    *args : TYPE
        所需属性或函数（类中存在的，输入属性名、函数名即可）
    ds : TYPE, optional
        额外可用变量（优先级更高，可自行修改优先级），供操作函数使用，默认可用此文件全局变量. The default is {}.
    get_runs : TYPE, optional
        是否返回操作字符串列表. The default is False.
    **kwargs : 字典值获得对应属性所需操作，可为表达式，默认参数以字典形式写在“//ks//”之后，在ds中输入相应变量可替代默认参数
            非自身类函数调用时及自身在dic、kwargs中定义的属性调用时，src不可省略。
            必须使用src代表源数据。

            合并属性返回类型为list. e.g.'raster_size': ('height', 'width') -> [900, 600]
            如需特定属性请用函数. e.g. 'raster_size': r"(src.height, src.width)" or r"pd.Serise([src.height, src.width])"

    Returns
    -------
    if get_runs:返回操作字符串列表
    else:args对应属性值列表

    '''
    
    ds.update({'src':src})
    
    # ds,接收上一文件的(全局、参数)变量,注销此段，则输入变量优先级更高。
    globals_old = set(ds)
    globals_now = set(globals())
    need_add = globals_old-globals_now
    data = {k:ds[k] for k in need_add}
    ds = data
    
    
    # 对需要的操作（run）进行整理
    runs = []
    for arg in args:
        try:
           # 跳过unhashable type, e.g. list、set
           arg in {}
        except:
           pass
        else:
            # 自定义属性处理
            add_attr = {k:v for k,v in kwargs.items() if f'src.{k}' in arg}
            # n = 0
            while ((arg in kwargs) or add_attr):
                try:
                    
                    arg = kwargs[arg]
                    add_attr = {k:v for k,v in kwargs.items() if f'src.{k}' in arg}
                except:
                    # 需要函数表达式操作的属性
                    for attr,attr_run in add_attr.items(): 
                        
                        ## 如果存在这个属性且不修改(not amend)则跳过
                        # if hasattr(src, attr) & (not(amend)):
                        #     continue
                        
                        # 调用getattrs获得属性
                        attr_value = getattrs(src,attr_run,ds=ds,**kwargs)
                        
                        # 为源数据添加属性------1/2
                        setattr(src,attr,attr_value)
                        
                        ## 不会改变源数据，而是更新表达式及可用变量集(ds)------1/2
                        # arg = arg.replace(attr,f'__attr{n}')
                        # ds.update({f'__attr{n}':attr_value})
                        # n += 1
                    break
        

        if isiterable(arg) & (type(arg) != str):
            # 递归
            run = getattrs(src, *arg, get_runs=True, **kwargs)
        else:
            # 参数处理
            if (r'//ks//' in arg):
                arg,ks = arg.split(r'//ks//')
                
                ks = eval(ks)  #<<<<<<取出默认参数
                ks.update(ds)  #<<<<<<输入参数覆盖默认参数
                ds = ks 
            
            
            # 整理run
            # 为源数据添加属性------2/2
            run = f'src.{arg}' if not ('src' in arg) else arg
            
            ## 不会改变源数据，而是更新表达式及可用变量集(ds)------2/2
            # run = f'src.{arg}' if (not ('src' in arg)) & (n==0) else arg
            
        runs.append(run)
    # 返回runs
    if get_runs:
        return runs
    # 调用批量操作函数
    else:
        return evals(*runs,**ds)
# getattrs.getattr

def add_attrs(src, run=False, ds={}, **attrs_dict):
    """
    向类（src）中添加属性

    Parameters
    ----------
    src : 输入类
    run : 是否启用表达式操作函数.  The default is False.
    ds : TYPE, optional
        表达式所需变量，为空则只有此文件全局变量可用. The default is {}.
    
    attrs_dict : (dict)
        属性：   对应操作表达式(run为True)
              or        对应值(run为False)

    Returns
    -------
    None.

    """
    
    
    for attr,attr_run in attrs_dict.items():
        if run:
            value = getattrs(src,attr_run,ds=ds,**attrs_dict)
        else:
            value = attr_run
        
        setattr(src,attr,value)





"""
字典相关函数
"""
        


def delete(dic,*ks,inplace=False):
    if inplace:
        for key in ks:
            if key in dic:
                del dic[key]
    else:
        dic1 = dic.copy()
        for key in ks:
            if key in dic1:
                del dic1[key]
        return dic1





# 查找
def findAll(target, dictData, notFound=[]):
    queue = [dictData]
    result = []
    while len(queue) > 0:
        data = queue.pop()
        for key, value in data.items():
            if key == target: result.append(value)
            elif type(value) == dict: queue.append(value)
    if not result: result = notFound
    return result

def find(target, dictData, notFound='没找到'):
    queue = [dictData]
    while len(queue) > 0:
        data = queue.pop()
        for key, value in data.items():
            if key == target: return value
            elif type(value) == dict: queue.append(value)
    return notFound



# 解包多重字典，未考虑重复项，如有重复取最深的一项
def ungroup(dictData,dtype = False):
    queue = [dictData]
    
    result = {}
    while len(queue) > 0:
        data = queue.pop()
        
        for key, value in data.items():
            
            if type(value) == dict: queue.append(value)
            elif dtype: 
                if type(value) == dtype: result[key] = value
            else: result[key] = value
    return result



def get_stop_first(date,stop):

    start_date = datetime.date(date.year,1,1)
    time_delta = datetime.timedelta(days=stop)
    
    while date >= start_date:
        date -= time_delta
    return date + time_delta

def get_stop_end(date,stop):

    end_date = datetime.date(date.year,12,31)
    time_delta = datetime.timedelta(days=stop)
    
    while date <= end_date:
        date += time_delta
    return date - time_delta


def get_stop_dates(start, end, stop, Year_all=True):
    
    start_date = start if type(start) == datetime.date else datetime.date(start)
    end_date = end if type(end) == datetime.date else datetime.date(end)
    
    if Year_all:
        start_date = get_stop_first(start_date, stop)
        end_date = get_stop_end(end_date, stop)
    
    time_delta = datetime.timedelta(days=stop)
    
    date_ls = []
    date = start_date
    while date <= end_date:
        date_ls.append(date)
        date += time_delta
    return date_ls

def wgt_from_conter(conter_array, lim=(0,1)):
    '''
    由中心点获取权重，默认数据已归一化

    Parameters
    ----------
    conter_array : TYPE
        中心点坐标array.
    lim : TYPE, optional
        上下限. The default is (0,1).

    Returns
    -------
    wgt : TYPE
        权重.

    '''
    lev = conter_array
    
    lev1 = np.append(2 * lim[1] - lev[0], lev)
    lev0 = np.append(lev1, lim[0] - lev1[-1])
    
    t = lev0[:-1] - lev0[1:]
    
    wgt = (t/2)[1:] + (t/2)[:-1]
    
    return wgt



def name_ext(path):
    # 获取文件名
    file_name_with_ext = os.path.basename(path)
    
    # 获取文件名和后缀
    file_name, file_extension = os.path.splitext(file_name_with_ext)
    
    
    return file_name, file_extension























if __name__ == 'main':
    import inspect
    current_line = inspect.currentframe().f_lineno
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        





































