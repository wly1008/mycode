
def read(raster_in,
         **kwargs):
    
    with rasterio.open(raster_in) as src:
        profile = src.profile
        arr = src.read(**kwargs)
        
        
        return arr, profile
