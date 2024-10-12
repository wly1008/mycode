def get_crs(gdf):
    import warnings
    warnings.filterwarnings('ignore')

    crs_dict = gdf.crs.to_dict()
    globe = ccrs.Globe(ellipse=crs_dict.get('ellps','WGS84'))
    if crs_dict['proj'] == 'longlat':
        return ccrs.PlateCarree(crs_dict.get('lon_0',0), globe)
    switch = {
        'aea': ccrs.AlbersEqualArea(crs_dict['lon_0'], crs_dict['lat_0'], crs_dict['x_0'], crs_dict['y_0'],
                                    (crs_dict['lat_1'], crs_dict['lat_2']), globe),
        'aeqd': ccrs.AzimuthalEquidistant(crs_dict['lon_0'], crs_dict['lat_0'], crs_dict['x_0'], crs_dict['y_0'],
                                          globe),
        'eqc': ccrs.PlateCarree(crs_dict['lon_0'], globe),
        'eqdc': ccrs.EquidistantConic(crs_dict['lon_0'], crs_dict['lat_0'], crs_dict['x_0'], crs_dict['y_0'],
                                      (crs_dict['lat_1'], crs_dict['lat_2']), globe),
        'lcc': ccrs.LambertConformal(crs_dict['lon_0'], crs_dict['lat_0'], crs_dict['x_0'], crs_dict['y_0'], None,
                                     (crs_dict['lat_1'], crs_dict['lat_2']), globe),
        'cea': ccrs.LambertCylindrical(crs_dict['lon_0'], globe),
        'merc': ccrs.Mercator(crs_dict['lon_0'], -80, 84, globe, None, crs_dict['x_0'], crs_dict['y_0'],
                              scale_factor=None),
        'longlat': ccrs.PlateCarree(crs_dict.get('lon_0',0), globe)
    }
    return switch[crs_dict['proj']]

    def add_north(ax, labelsize=18, loc_x=0.93, loc_y=0.9, width=0.04, height=0.09, pad=0.1):
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