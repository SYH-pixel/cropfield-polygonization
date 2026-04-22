from shapely.ops import split
from shapely.geometry import Point
from shapely.ops import nearest_points
from shapely import LineString
import pandas as pd

def poly_splitter(gdf, perimeter_column, geometry_column, delta):
    """
        This function splits a polygon at the narrowest point determined using a negative buffer. 

        Arguments: 
        gdf : Geodataframe
        perimeter_column : Name of column with perimeter values
        delta: buffer step (should be positive and in meters, project dataset if needed)

        Required packages: Shapely, pandas
        
        Other relevant packages: geopandas (geodataframe creation and loading), os (directory navigation)
    """
    gdf = gdf.copy()
    gdf['sdist'] = None
    gdf['buffers_geom'] = None
    gdf['buffer_geom1'] = None
    gdf['buffer_geom2'] = None
    gdf['pinch1'] = None
    gdf['pinch2'] = None
    gdf['line'] = None
    gdf['cut_geom1'] = None
    gdf['cut_geom2'] = None

    for idx, row in gdf.iterrows():
        max_len = gdf.at[idx, perimeter_column]
        current_buff = 0
        while current_buff <= max_len:
            current_buff += delta
            buffered = row[geometry_column].buffer(-current_buff)
            if buffered.geom_type == 'MultiPolygon':
                geoms = list(buffered.geoms)
                print(f"Split at row {idx}, buffer distance {current_buff:.3f}")
                gdf.at[idx, 'buffers_geom'] = buffered
                gdf.at[idx, 'sdist'] = -current_buff  # keep negative to match original
                gdf.at[idx, 'buffer_geom1'] = geoms[0]
                gdf.at[idx, 'buffer_geom2'] = geoms[1]
                break
        else:
            print(f"No split for row {idx} within max_len={max_len}")

    # Connecting narrowest part
    for idx, row in gdf.iterrows():
        if pd.isna(row['sdist']):
            continue
        else:
            p1, p2 = nearest_points(row['buffer_geom1'], row['buffer_geom2'])
            gdf.at[idx, 'pinch1'] = p1
            gdf.at[idx, 'pinch2'] = p2
            gdf.at[idx, 'line'] = LineString([p1, p2])

    # Creating Cut Line (Perpendicular Line) and cutting
    for idx, row in gdf.iterrows():
        if pd.isna(row['sdist']):
            continue
        else: 
            bounds = gdf.at[idx, geometry_column].bounds
            dist = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
            point1 = gdf.at[idx, 'pinch1']
            point2 = gdf.at[idx, 'pinch2']
            dx = point1.x - point2.x
            dy = point1.y - point2.y
            midpoint = Point((point1.x + point2.x) / 2, (point1.y + point2.y) / 2)
            perp_slope = -(dx/dy)
            perp_line = LineString([(midpoint.x - dist, midpoint.y - perp_slope * dist), (midpoint.x + dist, midpoint.y + perp_slope * dist)])
            cut = split(gdf.at[idx, 'geometry'], perp_line)
            gdf.at[idx, 'cut_geom1'] = cut.geoms[0]
            gdf.at[idx, 'cut_geom2'] = cut.geoms[1]
