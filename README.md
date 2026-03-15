# cropfield-polygonization
Work related to crop field processing completed for ClarkU Fall26 Intro to Python Directed Study and Mapping Africa projects

# Notes on setup 
Large cropfield attribute files are under .gitattributes, to access please install LFS. 

# Background
This work is based on Mapping Africa work completed by Prof. Lyndon Estes's AgroImpacts Research crop at Clark University. As part of their research, they have used CNNs to generate cropfield polygons across the entirety of states such as Zambia using high resolution Planet Imagery.
This project is  performed in parallel with other projects also attempting to create country wide large area field boundary maps, such as Fields of the World. 
Below is an example of the code used by Fields of the World to generate vector files from raster imagery: 
https://github.com/fieldsoftheworld/ftw-baselines/blob/main/ftw_tools/postprocess/polygonize.py

One challenge of this work is the creation of false "thin-necked" polygons and false "islands" within cropfield polygons. See example image below with false islands circled in red and thin necks connecting separate fields outlined in blue. 

For our final project, we propose building upon this research by finding an algorithmic way to clean up these cropfield polygons. 

# Proposed Methodology
We hope to build upon existing Mapping Africa code that calculates shape statistics for polygons and saves new GeoJSON files with additional information. Examples of metrics included: area, compactness, interior_edge (perimeter to area ratio), fractal_dim. 
https://github.com/agroimpacts/instancemaker/blob/main/src/instancemaker/computeinstances.py

Using these statistics, we can isolate polygons with "thin necks" and split them along these locations. Below is an example of a similar problem being approached in R that we can use to guide our project.
https://gis.stackexchange.com/questions/333817/splitting-polygons-at-narrowest-part-using-r

Other possible functions we can generate for this project include a sampling function to randomly sample tiles throughout our country of interest. After creating a representative sampling of tiles in Zambia, we can then run our algorithm on the sampled tiles. This could save time and computational resources.

We can also generate an function that differences the original polygons from our newly generate polygons to see the change in cropland area after processing is applied. 

** I think zac had another function he was interested in?** 
