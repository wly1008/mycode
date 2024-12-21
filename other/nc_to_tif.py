# -*- coding: utf-8 -*-
import xarray as xr
import numpy as np
import rasterio
from rasterio.transform import from_origin
def nc_to_tif(ds_nc,
              vr=None,
              out_ph=None,
              loc_names=None,
              crs='EPSG:4326',
              dtype='float32',
              nodata=None,
              descriptions:list[str] | str=None):
    '''
    nc转tif
    仅限维度为二[lat,lon] --- [height, width]
    或维度大小为三[*, lat,lon] --- [count, height, width] 第三个维度将设为栅格波段维度
    *维度顺序不限将自动排序

    Parameters
    ----------
    ds_nc : xr.Dataset,xr.DataArray
        nc变量
    vr : str
        提取的变量, 当vr为None且ds_nc为xr.Dataset时，ds_nc=ds_nc.to_dstaarray()
    out_ph : str
        输出位置
    loc_names : dict, optional
        lon,lat的对应变量名,默认为lon,lat
        
        eg. {'lon':'longitude', 'lat':'latitude'}
        
    crs : str, dict, or CRS; optional
        空间参考. The default is 'EPSG:4326'.
    dtype :  str or numpy dtype, optional
        数据类型. The default is 'float32'.
    nodata : int, float, or nan; optional
        数据无效值.
    descriptions : list[str] | str ,optional
        波段名列表，维度为3时默认为波段维度data, 维度为2时默认为 None

    Returns
    -------
    if out_ph is None :
        return arr_vr, profile, descriptions(波段名)
    else:
        output tif and return out_ph

    '''
    
   
    if loc_names is None:
        loc_names = {}
    
    lon_name = loc_names.get('lon', 'lon')
    lat_name = loc_names.get('lat', 'lat')
    
    if not isinstance(ds_nc, xr.DataArray):
        if vr is None:
            ds_nc = ds_nc.to_dataarray()
        else:
            ds_nc = ds_nc[vr].dims
    else:
        pass
    
    # dims判断
    dims = list(ds_nc.dims)
    assert {lat_name,lon_name}.issubset(set(dims)) , '未找到代表lat、lon的维度，尝试重新定义loc_names参数'
    assert len(dims) <= 3, 'dims长度超限,期望长度2或3，得到%d。仅接受代表[lat, lon]或[band, lat, lon]维度组'%len(dims)
        
    # 维度排序, descriptions获取
    loc = [lat_name, lon_name]
    if len(dims) == 3:
        new_dims = [i for i in dims if i not in loc] + loc
        descriptions = (ds_nc[new_dims[0]].data.astype(str).tolist() if descriptions is None
                        else
                        descriptions)
        count = ds_nc[new_dims[0]].size
    else:
        new_dims = loc
        descriptions = ([None] if descriptions is None
                        else
                        descriptions)
        count = 1
    
    descriptions = ([descriptions] if isinstance(descriptions, str)
                    else
                    descriptions)
    assert len(descriptions) == count, 'descriptions长度%d与波段数%d不一致' % (len(descriptions), count)
    
    if dims != new_dims:
        ds_nc = ds_nc.transpose(*new_dims)
    
    
    # 获取经纬度序列
    lon = ds_nc[lon_name].data
    lat = ds_nc[lat_name].data
    
    # 获取分辨率
    res_lon = abs(lon[1] - lon[0])
    res_lat = abs(lat[1] - lat[0])
    
    # 计算栅格transform
    transform = from_origin(west=lon.min()-res_lon/2,
                            north=lat.max()+res_lat/2,
                            xsize=res_lon, ysize=res_lat)
    
    
    # 获取数据矩阵
    arr_vr = ds_nc.data

    
    # 统一为三维(count, height, width), 并获取shape
    if arr_vr.ndim == 2:
        arr_vr = np.array([arr_vr])
    count, height, width = arr_vr.shape
    
    
    # 检查经纬度方向, 保证lat递减, lon递增
    if lat[1] > lat[0]:
        arr_vr = np.flip(arr_vr,axis=1) 
    if lon[1] < lon[0]:
        arr_vr = np.flip(arr_vr,axis=2) 
    
    # 定义profile
    profile = {
        "driver": "GTiff",
        "dtype": dtype,
        "width": width,
        "height": height,
        "count": count,
        "crs": crs,
        "transform": transform,
        "nodata": nodata
    }
    
    if out_ph is None:
        return arr_vr, profile, descriptions
    else:
        # 输出
        with rasterio.open(out_ph, 'w', **profile) as dst:
            dst.write(arr_vr)
            
            dst.update_stats()  # raserio >= 1.4.0
            dst.descriptions = descriptions
            
        return out_ph





# ph_nc = r'F:/01beijingword/09CH4/xiugai/xFig/fig6/data/average_CH4_yearly_0.1.nc'


# ds_nc = xr.open_dataset(ph_nc).isel(time=0)


# # nc_to_tif(ds_nc,nodata=np.nan,out_ph=r'F:\01beijingword\data\nc3.tif')
# arr_vr, profile, descriptions = nc_to_tif(ds_nc,nodata=np.nan)







