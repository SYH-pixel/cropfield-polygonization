
from poly import poly_splitter 
import pandas as pd 
import geopandas as gpd

#trying another version
def poly_splitter_recursive(gdf, perimeter_column, geometry_column, delta, max_iter, iter = 0):
    """
        This function recurses the poly_splitter function a number of times determined by the max_iter 
        parameter. It then combines all split and original geometries into the geometry column. 
        This should be used instead of the poly_splitter function alone.

        Arguments: 
        gdf : Geodataframe
        perimeter_column : Name of column with perimeter values
        delta: buffer step (should be positive)
        max_iter: The number of times to recurse through the gdf. Recommended iterations are between 3-5. 
        It takes ~25 minutes to run this on all polygons in the `test_tile` in thinnecks.ipynb
        iter: Starting iteration (should be 0)

        Required packages: poly, pandas, geopandas
    """
    if iter >= max_iter:
        print(f"Max no. of iterations ({max_iter}) reached")
        return gdf

    gdf = gdf.reset_index(drop=True)

    res = poly_splitter(gdf, perimeter_column, geometry_column, delta)

    if res['cut_geom1'].isna().all():
        print(f"No more splits")
        return gdf

    final_split_geom = []
    split_index = []
    new_idx = len(gdf)  # start after existing rows

    for idx, row in res.iterrows():
        if pd.isna(res.at[idx, 'cut_geom1']): 
            continue
        split_index.append(idx)  #recording split indices

        row1 = row.copy()
        row1.name = new_idx
        row1[geometry_column] = res.at[idx, 'cut_geom1']
        row1[perimeter_column] = res.at[idx, 'cut_geom1'].length
        print(f"  storing row1: area={row1[geometry_column].area:.1f}, type={row1[geometry_column].geom_type}")
        new_idx += 1 # new idx for cut geom

        row2 = row.copy()
        row2.name = new_idx
        row2[geometry_column] = res.at[idx, 'cut_geom2']
        row2[perimeter_column] = res.at[idx, 'cut_geom2'].length
        print(f"  storing row2: area={row2[geometry_column].area:.1f}, type={row2[geometry_column].geom_type}")
        new_idx += 1

        final_split_geom.extend([row1, row2])

    gdf_unsplit = gdf.drop(index=split_index) # removing split indices from original index list
    final_geom_gdf = gpd.GeoDataFrame(final_split_geom, geometry=geometry_column, crs=gdf.crs)
    final_combined_gdf = pd.concat([gdf_unsplit, final_geom_gdf]) 

    return poly_splitter_recursive(final_combined_gdf, perimeter_column, geometry_column, delta, max_iter, iter + 1)