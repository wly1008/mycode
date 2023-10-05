def window(raster_in, shape=None, size=None, step=None, get_self_wins=False, initial_offset=None,Tqbm=False):
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
    # assert not(step) or (step and size), "请填入滑动窗口大小 size参数"
    
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
        # yend = ysize if (src.height - ysize) % ystep == 0 else (ysize - ((ystep - (src.height - ysize) % ystep)))
        yend = ysize - (ystep - (yend0 or ystep))
        xend = xsize - (xstep - (xend0 or xstep))

    else:
        # 规范变量
        xstep = None
        ystep = None
    
    initial_offset_x, initial_offset_y = initial_offset or (0,0)  # 初始偏移量
    
    # 返回值变量
    inxs = []  # 窗口位置索引（在shape中）
    # inx = {}
    windows = []
    if get_self_wins:
        self_windows = []
    
    '''
    #并行反而更慢
    # pool = ProcessPoolExecutor(11)
    # axis = 0
    # func = partial(get_wins,axis=axis,initial_offset=(initial_offset_x, initial_offset_y),end=(yend,xend),size=(ysize,xsize),step=(ystep,xstep),shape=shape,get_self_wins=get_self_wins)
    # result = list(tqdm(pool.map(func,range(shape[axis])),total=shape[axis]))
    # if get_self_wins:
    #     windows, inxs, self_windows = zip(*result)
    #     self_windows = list(chain(*self_windows))
    # else:
    #     windows, inxs = zip(*result)
    # windows = list(chain(*windows))
    # inxs = list(chain(*inxs))

    #循环
    # for i in range(shape[0]):
    #     if get_self_wins:
    #         windows0, inxs0, self_windows0 = get_wins(i,axis=0,initial_offset=(initial_offset_x, initial_offset_y),end=(yend,xend),size=(ysize,xsize),step=(ystep,xstep),shape=shape,get_self_wins=get_self_wins)
    #         self_windows.append(self_windows0)
    #     else:
    #         windows0, inxs0 = get_wins(i,axis=0,initial_offset=(initial_offset_x, initial_offset_y),end=(yend,xend),size=(ysize,xsize),step=(ystep,xstep),shape=shape,get_self_wins=get_self_wins)
    #     windows.append(windows0)
    #     inxs.append(inxs0)
    
    # windows = list(chain(*windows))
    # inxs = list(chain(*inxs))
    # if get_self_wins:
    #     self_windows = list(chain(*self_windows))
    '''
    # with tqdm(total=shape[0]*shape[1]) as pbar:
    if Tqbm:
        pbar = tqdm(total=shape[0]*shape[1])
    pbar.set_description('生成窗口')
    y_off = initial_offset_y  # y初始坐标
    for y_inx,ax0 in enumerate(range(shape[0])):
        
        x_off = initial_offset_x
        height = yend if ax0 == (shape[0] - 1) else ysize 
        if get_self_wins:
            self_height = yend if ax0 == (shape[0] - 1) else ystep
            
        for x_inx,ax1 in enumerate(range(shape[1])):

            width = xend if ax1 == (shape[1] - 1) else xsize
            if get_self_wins:
                self_width = xend if ax1 == (shape[1] - 1) else xstep
            
            windows.append(Window(x_off, y_off, width, height))
            if get_self_wins:
                self_windows.append(Window(x_off, y_off, self_width, self_height))
            
            '''
            # 窗口位置索引（在输入栅格矩阵中）
            start = x_off
            end = x_off + width
            inx['x'] = (start, end)

            start = y_off
            end = y_off + height
            inx['y'] = (start, end)

            inxs.append(inx.copy())
            '''
            inxs.append((y_inx,x_inx))
            
            x_off += xstep or width
            if Tqbm:
                pbar.update(1)

        
        y_off += ystep or height
    if Tqbm:
        pbar.close()

    return (windows, inxs) if not get_self_wins else (windows, inxs, self_windows)
