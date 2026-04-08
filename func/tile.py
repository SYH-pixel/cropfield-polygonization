## Tile sampler function. See tile_test.ipynb for more documentation.
import numpy as np

def tile_sampler(gdf, tile_column, area_column, no_tiles, seed):
    """
        This function returns all polygons in randomly selected tiles. Tile selection probability is cropland area weighted.

        Arguments: 
        gdf : Geodataframe
        tile_column : Name of column with tile identifier numbers
        area_column : Name if column with crop polygon area values
        no_tiles : Number of tiles to be sampled 
        seed : Seed value for reproducibility

        Required packages: numpy
        
        Other relevant packages: geopandas and pandas (geodataframe creation and loading), os (directory navigation)
    """
    
    if seed is not None:
        np.random.seed(seed)

    tile_weights = gdf.groupby(tile_column)[area_column].sum() 
    tile_weights = tile_weights / tile_weights.sum()
    
    if no_tiles > len(tile_weights): 
        raise ValueError(f"Sample size is greater than total number of tiles.")

    tile_sample = np.random.choice(
        tile_weights.index, 
        size = no_tiles, 
        replace = False, 
        p = tile_weights.values
    )

    return gdf[gdf[tile_column].isin(tile_sample)]