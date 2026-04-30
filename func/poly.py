from shapely.ops import split
from shapely.geometry import Point
from shapely.ops import nearest_points
from shapely import LineString
import pandas as pd
from shapely.ops import unary_union
from shapely.affinity import scale
from numpy import sqrt
from shapely.ops import snap

def poly_splitter(gdf, perimeter_column, geometry_column, delta):
    """
        This function splits a polygon at the narrowest point determined using a negative buffer. 

        Arguments: 
        gdf : Geodataframe
        perimeter_column : Name of column with perimeter values
        delta: buffer step (should be positive)

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
            if buffered.geom_type == 'MultiPolygon' and current_buff > 0.2:
                geoms = list(buffered.geoms)
                print(f"Split at row {idx}, buffer distance {current_buff:.3f}")

                gdf.at[idx, 'buffers_geom'] = buffered
                gdf.at[idx, 'sdist'] = -current_buff 
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
            dist = max(bounds[2] - bounds[0], bounds[3] - bounds[1])/4 # Arbitrary division to reduce sliver generation

            point1 = gdf.at[idx, 'pinch1']
            point2 = gdf.at[idx, 'pinch2']

            dx = point1.x - point2.x
            dy = point1.y - point2.y
            length = sqrt(dx**2 + dy**2)
            perp_dx = -dy / length  # perpendicular unit vector
            perp_dy = dx / length   

            # x/y unit vectors used as a factor to multiply dist by and extent cutting line past polygon exterior 
            midpoint = Point((point1.x + point2.x) / 2, (point1.y + point2.y) / 2)
            perp_line = LineString([(midpoint.x - dist * perp_dx, midpoint.y - perp_dy * dist ), (midpoint.x + dist * perp_dx, midpoint.y + perp_dy * dist)])

            # large tolerance because some cut lines were intersecting the polygon at a point and not splitting correctly. This may need to be fine tuned more
            snapped_line = snap(perp_line, gdf.at[idx, geometry_column], tolerance=1.0) 
            cut = split(gdf.at[idx, geometry_column], snapped_line)

            if len(cut.geoms) == 1: #"failed" cut
                gdf.at[idx, 'sdist'] = None 
                gdf.at[idx, 'cut_geom1'] = None
                gdf.at[idx, 'cut_geom2'] = None

            if len(cut.geoms) == 2:
                sorted_geoms = sorted(cut.geoms, key=lambda g: g.area, reverse=True)
                gdf.at[idx, 'cut_geom1'] = sorted_geoms[0]
                gdf.at[idx, 'cut_geom2'] = sorted_geoms[1]
                
            elif len(cut.geoms) > 2: # need to account for extra accidental splits for areas near the split line
                sorted_geoms = sorted(cut.geoms, key=lambda g: g.area, reverse=True)
                big1, big2 = sorted_geoms[0], sorted_geoms[1]
                slivers = sorted_geoms[2:]  # everything after the top 2
                merge_with_1 = [big1]
                merge_with_2 = [big2]
        
                for sliver in slivers:
                    sharededge1 = big1.intersection(sliver).length # shared edge between sliver and "majority" p9ieces
                    sharededge2 = big2.intersection(sliver).length
                    
                    if sharededge1 == sharededge2: # if sliver has same sharededge length with all larger pieces (usually split at a point), go with closer piece
                        if big1.distance(sliver) <= big2.distance(sliver):  
                            merge_with_1.append(sliver)
                        else:
                            merge_with_2.append(sliver)
                    elif sharededge1 >= sharededge2:
                        merge_with_1.append(sliver)
                    else:
                        merge_with_2.append(sliver)
                gdf.at[idx, 'cut_geom1'] = unary_union(merge_with_1)
                gdf.at[idx, 'cut_geom2'] = unary_union(merge_with_2)

    return gdf