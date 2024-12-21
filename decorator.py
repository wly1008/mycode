# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 11:40:41 2023

@author: wly
"""
from mycode._Raster import check,get_RasterAttr,unify,create_raster,reproject,window
from mycode.codes import *
from mycode.models import *
from mycode._Class import raster




def _Type_args_(Type,args=[]):
    '''
    一般在获得参数提示信息中使用，获得参数提示中包含的类

    Parameters
    ----------
    Type : TYPE
        类
    args : TYPE, optional
        在此表基础上添加类，为配合递归使用，调用时请手动设置为[],使用默认值在某些时候args不在下次调用前清零（暂未检查原因）

    Returns
    -------
    args : TYPE
        包含的类

    '''
    # 先加上本身
    args.append(Type)
    if isinstance(Type, (list,tuple)):
        for arg in Type:
            args = _Type_args_(arg,args=args)
    try:
        # 取出集合类中包含的类
        for arg in tuple(Type.__args__):
            args.append(arg)
            # 提示中可用的特性集合类在typing、types中
            if type(arg) in [i[1] for i in inspect.getmembers(typing)] + [i[1] for i in inspect.getmembers(types)]:
                # 递归
                args = _Type_args_(arg,args=args)
    except AttributeError:
        pass
    return args

def _Type_args_names(Type):
    '''
    一般在获得参数提示信息中使用，获得参数提示中包含的类名

    Parameters
    ----------
    Type : TYPE
        类

    Returns
    -------
    names : TYPE
        包含的类名

    '''
    args = _Type_args_(Type,[])
    names = []
    for arg in args:
        # 一些类没有__name__属性，手动处理
        try:
            names.append(arg.__name__)
        except AttributeError:
            names.append(str(type(arg)).split('\'')[-2].split(".")[-1])  
    return names


def arg_tidy(fn,*args,full=False,**kwargs):
    '''
    整理输入参数，除可变参数，其余放入kwargs中
    
    Parameters
    ----------
    fn : TYPE
        使用的函数
    *args ,**kwargs : TYPE
        接收所有参数
    full : bool
        是否填充默认参数

    Returns
    -------
    args: tuple
        可变参数
    kwargs : dict
        参数字典

    '''
    #
    if not any(args):
        args = ()
        
    else:
        ArgSpec = inspect.getfullargspec(fn)  # 参数信息
    
        if ArgSpec[1]:
            # 可变参数存在时
            loc = ArgSpec[0]
            # 分离必填参数与可变参数
            kwargs.update({loc[i]:args[i] for i in range(len(loc))})
            args = args[len(loc):]
        else:
            loc = ArgSpec[0]
            kwargs.update({loc[i]:args[i] for i in range(len(args))})
            args = ()
    
    if full:
        ArgSpec = inspect.getfullargspec(fn)
        loc_name = ArgSpec[0] # 位置参数
        def_value = ArgSpec[3]  # 默认参数默认值
        
        # 默认参数字典
        if def_value:
            def_dict = {loc_name[i]:def_value[i] for i in range(-1,-len(def_value)-1,-1)}
        else:
            def_dict = ArgSpec[5]  # 存在可变参数 * 时，def_value=None,def_dict = ArgSpec[5]
        all_kwargs = def_dict
        all_kwargs.update(kwargs)
        kwargs = all_kwargs
    return args,kwargs




def runtime(fn):

    '''
    装饰器
    为函数添加运行时间打印
    
    Parameters
    ----------
    fn : function
        需要添加打印运行时间的函数

    Returns
    -------
    newfunc.
    
    
    '''
    @wraps(fn)
    def newfunc(*args,**kwargs):
        s = time.time()
        re = fn(*args,**kwargs)
        print('运行时间：%.2f'%(time.time()-s)+'s')
        return re
    return newfunc

def unify_project(dst:str=None,dst_list:str=None,dst_crs:CRS=None):
    '''
    获得统一参数空间参考的装饰器，请在需要统一的参数后加上类型提示--->para:raster
    raster可以自己定义一个简单的类，这里只做标识作用

    Parameters
    ----------
    dst : str
        目标参数名，空间参考以此为准
    dst_list: str
        目标参数名(变量类型为list or tuple)，请保证列表中栅格数据空间参考统一
    dst_crs: CRS
        目标空间参考，优先级最高，但建议三个参数只填一个
        
    
    Raises
    -------
    dst,dst_list,dst_crs必须输入其中一个

    Returns
    -------
    TYPE func(decorator)
        装饰器，统一函数中的栅格参数的空间参考

    '''
    
    if not any((dst,dst_list,dst_crs)):
        raise Exception('dst,dst_list,dst_crs必须输入其中一个')
    
    
    
    
    def try_reproject(src, dst=None, crs=None, *args,**kwargs):
        '''
        尝试使用resproject,失败者返回原值

        '''
        # 递归，批量操作
        if isinstance(src, (list,tuple)):
            return [try_reproject(i) for i in src]
        try:
            return reproject(raster_in=src,dst_in=dst,crs=crs,*args,**kwargs)
        except:
            return src
    
    
    def para_reproject(fn):
        '''
        装饰器，统一函数中的栅格参数空间参考

        Parameters
        ----------
        fn : func
            被装饰函数.

        Returns
        -------
        TYPE func
            被装饰后的函数

        '''
        
# =============================================================================
#         # 获得原函数的参数信息
# =============================================================================
        ArgSpec = inspect.getfullargspec(fn)
        loc_name = ArgSpec[0]
        args_name = ArgSpec[1]
        kwargs_name = ArgSpec[2]
        def_name = ArgSpec[4]
        
        
        args_cla = {k:_Type_args_names(v) for k,v in ArgSpec[-1].items()} #<<<<<<获得参数的提示类
        args_raster = [k for k,v in args_cla.items() if 'raster' in v]  #<<<<<<获得标识了raster类的参数
        @wraps(fn)
        def newfunc(*args,**kwargs):
            args_ti,kwargs_ti = arg_tidy(fn, *args, **kwargs)  #<<<<<<整理输入参数，除可变参数，其余放入kwargs中
            
# =============================================================================
#             # 获得空间参考
# =============================================================================
            
            if dst_crs:  # <<<<<<如果输入的是空间参考
                crs = dst_crs  ##<crs>##
            else:
                
                dst_value = kwargs_ti[dst]
                if isinstance(dst_value, (list,tuple)):  #<<<<<< 如果目标是列表
                    if dst_list: # <<<<<<期望输入的就是列表
                        crs = get_RasterAttr(dst_value[0],'crs')  ##<crs>##
                        
                        # 检验列表中的空间参考是否统一
                        if False in [get_RasterAttr(i,'crs')==crs for i in dst_value]:
                            raise Exception('目标列表栅格空间参考不统一')
                            
                    else: # <<<<<<期望输入的是单个数据
                        # 可能是批量操作让它原样返回

                        return fn(*args,**kwargs)
                else:
                    crs = get_RasterAttr(dst_value,'crs')  ##<crs>##
            
            
# =============================================================================
#             # 对标识了raster参数进行重投影
# =============================================================================
            
            # 如果可变参数里存在raster
            if args_name in args_raster:
                args_ti = [try_reproject(i,crs=crs) for i in args_ti]  # <<<<<<重投影
            
            # 必选参数、默认参数中的raster处理
            kwargs_ti.update({k:try_reproject(v,crs=crs)
                           for (k,v) in kwargs_ti.items() if (k in args_raster)&(k != dst)&(k != dst_list)})  # <<<<<<重投影
            loc_para = [kwargs_ti.pop(k) for k in loc_name if k in kwargs_ti]  # <<<<<<取出位置参数
            def_para = {k:kwargs_ti.pop(k) for k in def_name if k in kwargs_ti}  # <<<<<<取出默认参数
            
            # 如果关键词参数里存在raster
            if kwargs_name in args_raster:
                kwargs_ti = {k:try_reproject(v,crs=crs) for (k,v) in kwargs_ti.items()}  # <<<<<<重投影
            
# =============================================================================
#             # 将处理好的参数输入原函数中
# =============================================================================
            return fn(*loc_para, *args_ti, **def_para, **kwargs_ti)
        return newfunc
            


    return para_reproject




def _return(out_path=None,get_ds=True,arr=None,profile=None,ds=None):
    
    if ds:
        ds = rasterio.open(ds) if isinstance(ds, (str,pathlib.Path)) else ds
        profile = ds.profile
        arr = ds.read()
    
    if out_path:
        out(out_path=out_path,data=arr, profile=profile)
        
    elif get_ds:
        ds = create_raster(**profile)
        ds.write(arr)
        return ds
    else:
        return arr,profile




def unrepe(src:str,attrs:List[str],
            moni_args:List[str]=[], moni_kwargs:dict={}, moni_kwargs_how:bool=False,
            dst:str=None, dst_attrs:List[str]=None, dst_attrs_need:List[object]=None,
            return_and_dict:[list,tuple]=(_return,{'ds':'raster_in'},{})
            ):
    '''
    生成跳过重复操作的装饰器

    Parameters
    ----------
    src : str
        处理参数名
    attrs : List[str]
        处理属性列表
    moni_args : List[str]
        监控的默认变量是否变动，变动则正常运行
    moni_kwargs : dict
        监视的变量是否在设定值集中
    moni_kwargs_how : bool
        配合moni_kwargs
        False : 不在则正常运行;
        True : 在则正常运行
    
    dst : str, optional
        目标参数名
    dst_attrs : List[str], optional
        目标属性参数名列表（与attrs长度顺序对应）
       
    dst_attrs_need : List[object]
        固定属性列表（这填入的是值）
    return_and_dict : [list,tuple], optional
        重复时的输出函数.
        
        如填入None,则输出源数据
        (函数,{返回函数参数名:输入函数参数名},{返回函数参数名:参数设置值}（优先级高）)
        The default is (_return,{'ds':'src'},{}).
    

    Raises
    ------
    Exception
        DESCRIPTION.

    Returns
    -------
    跳过重复操作的装饰器

    '''
    
    if not any((dst,dst_attrs)):
        raise Exception('dst,dst_attrs,dst_attrs_need必须输入其中一个')
    
    def check_repe(fn):
        '''
        跳过重复操作的装饰器
        '''
        
        ArgSpec = inspect.getfullargspec(fn)
        loc_name = ArgSpec[0] # 位置参数
        args_name = ArgSpec[1]  # 可变参数 *
        kwargs_name = ArgSpec[2]  # 可变参数 **
        def_value = ArgSpec[3]  # 默认参数默认值
        def_name = ArgSpec[4]  # 关键字参数
        
        # 默认参数字典
        if def_value:
            def_dict = {loc_name[i]:def_value[i] for i in range(-1,-len(def_value),-1)}
        else:
            def_dict = ArgSpec[5] 

        
        @wraps(fn)
        def newfunc(*args,**kwargs):
            args_ti,all_kwargs = arg_tidy(fn, *args, **kwargs,full=True)  #<<<<<<整理输入参数，除可变参数，其余放入kwargs中

# =============================================================================
#             判断是否需要运行
# =============================================================================
            
            # 监控的默认变量是否变动，变动则正常运行
            if False in [all_kwargs[i] == def_dict[i] for i in moni_args]:
                
                return fn(*args,**kwargs)
            
            # 监视的变量是否在设定值集中。moni_kwargs_how=False不在则正常运行;moni_kwargs_how=True在则正常运行
            if moni_kwargs_how in [all_kwargs[i] in moni_kwargs[i] for i in moni_kwargs]:
                
                return fn(*args,**kwargs)
                

            # 比较待操作的属性，属性不同则正常运行
            
            if dst:
                # 这里调用arcmap.check函数，是基于get_RasterAttr,如处理其他数据，可用getattrs重写获取属性与检查函数
                dst_in = all_kwargs[dst]
                if dst_in:
                    judge,dif = check(raster_in=all_kwargs[src], dst_in=dst_in, need=attrs)
            
            if dst_attrs:
                dst_attrs_value = [all_kwargs[k] for k in dst_attrs if k in all_kwargs]
                
                for i in range(len(dst_attrs_value)):
                    dst_attr = dst_attrs_value[i]
                    need = attrs[i]
                    if dst_attr:
                        judge,dif = check(raster_in=all_kwargs[src], dst_attrs=[dst_attr],need=[need])
                        if not judge:  # <<<<<<有False就跳出
                            break

            if dst_attrs_need:
                judge,dif = check(raster_in=all_kwargs[src], dst_attrs=dst_attrs_need,need=attrs)
            
            if not judge: # 属性不同则正常运行
                return fn(*args,**kwargs)
            
            
# =============================================================================
#             三个条件都不符合则调用返回函数
# =============================================================================

            # 整理返回函数---> 函数，{返回函数参数名:输入函数参数名}，{返回函数参数名:参数设置值}（优先级高）
            
            if return_and_dict is None:
                # print("return")
                return all_kwargs[src] # 如填入None,则输出源数据
            
            elif callable(return_and_dict):
                return_fn,return_dict,return_kwargs = return_and_dict,{},{}
            elif len(return_and_dict) == 3:
                return_fn, return_dict, return_kwargs = return_and_dict
            elif len(return_and_dict) == 2:
                (return_fn, return_dict), return_kwargs = return_and_dict, {}
            elif len(return_and_dict) == 1:
                return_fn, return_dict, return_kwargs = return_and_dict[0],{},{}
            else:
                raise Exception("return_and_dict有误")

            
            # 设置返回函数参数
            kwargs_return = {}  # 设置默认参数,*args,**kwargs的参数没有填入，直接加入有点怕会乱了返回函数，如果需要自行修改
            
            kwargs_return.update({k: v for k, v in all_kwargs.items()
                                    if k in inspect.getfullargspec(return_fn)[0] + inspect.getfullargspec(return_fn)[4]})  #接收其他参数
            for k in return_dict:
                kwargs_return[k] = all_kwargs[return_dict[k]]
            
            kwargs_return.update(return_kwargs)

            return return_fn(**kwargs_return)
        
        return newfunc
    
    
    return check_repe
    






def split_window(*rasters):
    

    
    def wrapping(fn):
        
        
        def newfunc(*args,**kwargs):
            
            dst = cd.get_first(rasters,)
            
            
            
        
        
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
            pass



# #@unify_project(dst='raster_in')
@unrepe(src='raster_in',attrs=['Bounds'],dst='dst_in',dst_attrs=['bounds'],moni_kwargs={'Extract':(0,False,None,(),{})})
def clip1(raster_in:raster,*args,
          dst_in:raster=None, bounds=None,
          inner=False,
          Extract=False,mask=False,
          out_path=None, get_ds=True):
    '''
    和原函数_clip一样，只是尝试调用其他函数

    '''
    # _clip有批量处理操作，但直接调用，单个运行会在_clip处，哪里没有装饰器，无法统一投影
    if isinstance(raster_in, (list,tuple)):
        if out_path is None:
            out_path = [None for i in range(len(raster_in))]
        if len(out_path) != len(raster_in):
            raise Exception('输入栅格与输出路径数量不一致')
        return [clip1(raster_in=_src,
                      dst_in=dst_in, bounds=bounds,
                      inner=inner,
                      Extract=Extract, mask=mask,
                      out_path=_out_path, get_ds=get_ds) for _src,_out_path in zip(raster_in,out_path)]

    return _clip(raster_in=raster_in,
                dst_in=dst_in, bounds=bounds,
                inner=inner,
                Extract=Extract,mask=mask,
                out_path=out_path, get_ds=get_ds)










if __name__ == '__main__':
    import time
    raster_in = r'F:/PyCharm/pythonProject1/arcmap/015温度/土地利用/landuse_4y/1981-5km-tiff.tif'
    
    dst_in = r'F:\PyCharm\pythonProject1\arcmap\007那曲市\data\eva平均\eva_2.tif'
    
    out_path = r'F:\PyCharm\pythonProject1\代码\mycode\测试文件\1981-5km-tiff13.tif'
    
    out_path1 = r'F:\PyCharm\pythonProject1\arcmap\015温度\zonal\grand_average.xlsx'
    
    s = time.time()
    ds = unify(raster_in,dst_in)
    print('运行时间：%.2f'%(time.time()-s)+'s')
    s = time.time()
    # # ds1 = clip1(raster_in, dst_in=dst_in)
    ds1 = clip1(ds, dst_in=dst_in)
    ds1 = clip1(ds, dst_in=dst_in,Extract=0)
    ds1 = clip1(ds, bounds=[85.052555, 29.935457, 95.052555, 36.485457])
    ds1 = clip1(ds, bounds=[85.052555, 29.935457, 95.052555, 36.485457])
    ds1 = clip1(ds, bounds=[85.052555, 29.935457, 95.052555, 36.485457])
    

    print('运行时间：%.2f'%(time.time()-s)+'s')
















































