import shapefile as shp
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import LineCollection
from shapefile import Reader
import cartopy.crs as ccrs
import copy
import geopandas as gpd




# import matplotlib.path as mpath
# import matplotlib.patches as mpatches
# import matplotlib.collections as mcollections

# def shpclip(originfig, ax, shpfile, column_index, region='China', cover=True, crs=None):
#     # 读取shapefile
#     gdf = gpd.read_file(shpfile)
    
#     # 如果没有指定CRS，则尝试自动检测
#     if crs is not None:
#         gdf = gdf.to_crs(crs)
    
#     # 找到与给定区域名匹配的几何体
#     if cover or (region in gdf.iloc[:, column_index].unique()):
#         matching_regions = gdf[gdf.iloc[:, column_index] == region]
#         if len(matching_regions) > 0:
#             # 将所有多边形组合成一个MultiPolygon
#             multi_polygon = matching_regions.unary_union
            
#             # 将GeoPandas中的MultiPolygon转换为matplotlib Path
#             vertices = []
#             codes = []
#             for poly in multi_polygon.geoms:
#                 for ring in [poly.exterior] + list(poly.interiors):
#                     codes += [mpath.Path.MOVETO]
#                     for point in ring.coords[:-1]:
#                         vertices.append(point)
#                     codes += [mpath.Path.LINETO] * (len(ring.coords) - 2)
#                     codes += [mpath.Path.CLOSEPOLY]
            
#             clip = mpath.Path(vertices, codes)
#             clip_patch = mpatches.PathPatch(clip, transform=ax.transData, facecolor='none', edgecolor='none')
#             ax.add_patch(clip_patch)
            
#             # 将clip应用到所有的collections
#             for collection in originfig.collections:
#                 collection.set_clip_path(clip_patch)
                
#     return clip_patch










def shp2clip(originfig,ax,shpfile,i,region = 'China',cover=True,crs=None):

    sf = shp.Reader(shpfile,encoding='utf-8')
    for shape_rec in sf.shapeRecords():
        if (shape_rec.record[i] == region) or cover:  ####这里需要找到和region匹配的唯一标识符，record[]中必有一项是对应的。
            vertices = []
            codes = []
            pts = shape_rec.shape.points
            prt = list(shape_rec.shape.parts) + [len(pts)]
            for i in range(len(prt) - 1):
                for j in range(prt[i], prt[i+1]):
                    vertices.append((pts[j][0], pts[j][1]))
                codes += [Path.MOVETO]
                codes += [Path.LINETO] * (prt[i+1] - prt[i] -2)
                codes += [Path.CLOSEPOLY]
            clip = Path(vertices, codes)
            clip = PathPatch(clip, transform=ax.transData)

    for contour in originfig.collections:
        contour.set_clip_path(clip)
    return clip

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




