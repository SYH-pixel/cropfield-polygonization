# -*- coding: utf-8 -*-

#C:\Users\owner\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3 ------>folder with ArcPy executable file
import arcpy 
print(arcpy.__file__)

#================
#Input variables
#================
#Structure of topology pulled from ArcGIS Pro documentation: https://pro.arcgis.com/en/pro-app/latest/help/data/topologies/creating-a-topology.htm
#input_fc is a string of the feature class (only one used here) to be added to the topology, with the the xy_rank and z_rank parameters which specify the rank of the feature class in the topology and determines how it is processed during validation.
#Rules chosen from ArcGIS Pro Toolbox; does not appear to be pre-made topology rule for small island detection or hole indexing, so this is done in post-processing.
input_dataset = r"D:\GraduateSchool\Masters\MsGIS\ClarkU\Classes\2026_A_Spring\GEOG_DS_Intro_Python_Programming\Mapping_Africa_project\Intro_Python_Mapping_Africa_Map\Intro_Python_Mapping_Africa_Map.gdb\SampleArea_Topology_Test" 
topo_name = "Sample_Area_Topology_Test"
cluster_tol = 0.001
input_fc = r"D:\GraduateSchool\Masters\MsGIS\ClarkU\Classes\2026_A_Spring\GEOG_DS_Intro_Python_Programming\Mapping_Africa_project\Intro_Python_Mapping_Africa_Map\Intro_Python_Mapping_Africa_Map.gdb\SampleArea_Topology_Test\SampleArea_Mungaila_UTM35S 1 1"
rules = r"'Must Not Overlap (Area)' D:\GraduateSchool\Masters\MsGIS\ClarkU\Classes\2026_A_Spring\GEOG_DS_Intro_Python_Programming\Mapping_Africa_project\Intro_Python_Mapping_Africa_Map\Intro_Python_Mapping_Africa_Map.gdb\SampleArea_Topology_Test\SampleArea_Mungaila_UTM35S # D:\GraduateSchool\Masters\MsGIS\ClarkU\Classes\2026_A_Spring\GEOG_DS_Intro_Python_Programming\Mapping_Africa_project\Intro_Python_Mapping_Africa_Map\Intro_Python_Mapping_Africa_Map.gdb\SampleArea_Topology_Test\SampleArea_Mungaila_UTM35S #"
validate = "true"

#====================
# Create the topology
#====================
#creates topology inside the feature dataset based on the above defined variables
out_topo = arcpy.CreateTopology_management(input_dataset, topo_name, cluster_tol)
print("Created topology.")

#======================================================================
# Loop through the list of feature classes and add them to the topology
#======================================================================
#splits the features listed in input_fc into a list using the ";" separator (this topology only has one feature as of now so currently unnecessary but kept in for future use)
#set up for loop to itterate through the above list and split each feature into its component parameters (feature class, xy_rank, z_rank (which is not used in this topo)) 
#assigns parameters to variables
#adds these feature class(es) to the topology using the AddFeatureClassToTopology_management function
input_fcL = input_fc.split(";")
for fc in input_fcL:
    param = fc.rsplit(" ", 2)
    in_fc = param[0]
    xy_rank = param[1]
    z_rank = param[2]
    arcpy.AddFeatureClassToTopology_management(out_topo, in_fc, xy_rank, z_rank)
    print(arcpy.GetMessages())

#=============================================================   
# Loop through the list of rules and add rules to the topology
#=============================================================
#splits rules into a list using the ";" separator; this topo only has the one rule so currently unnecessary but kept in for future use
#sets up for loop to itterate through the above list and split each rule into its component parameters (rule type, in_fc1, subtype1, in_fc2, subtype2); there is only one feature class in this topo so the in_fc2 and subtype2 parameters are not used but kept in for future use
#assigns parameters to variables
#adds this rule(s) to the topology using the AddRuleToTopology_management function
rulesL = rules.split(";")
for rule in rulesL:
    r = rule.rsplit(" ", 4)
    rule_type = r[0].replace("'","") #removes quotes from rule name
    in_fc1 = r[1]
    subtype1 = r[2]
    in_fc2 = r[3]
    subtype2 = r[4]
    arcpy.AddRuleToTopology_management(out_topo, rule_type, in_fc1, subtype1, in_fc2, subtype2)
    print(arcpy.GetMessages())

#======================    
# Validate the topology
#======================
#confirms that the validation is enabled before running the validation process
#runs the topology created and saved into the feature dataset
#print errors if validation fails
#print val complete if validation succeeds without errors
if validate == "true":
    try:
        arcpy.ValidateTopology_management(out_topo)
    except:
        print(arcpy.GetMessages()) 


print("Topology Validation Complete.")




#=======================
#=======================
#Post-Processing Section
#=======================
#=======================



#=======================
#Small Island Detection
#=======================
#using make feature layer function to create a new feature class from the above defined input feature class to bridge between original fc and new output of small island polygons
#-->Make feature layer here because certain python functions require a feature layer as input; this creates a feature layer from the holes feature class if needed for further processing
#using select by attribute to select polygons with an area less than 300 square-meters; 300m threshold chosen based on visual assessment; can be changed as needed
#using copy features to create a new feature class from the temp layer of the small island polygons
#using get count to count the number of small island polygons and print the result
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/make-feature-layer.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-attribute.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/copy-features.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/get-count.htm
arcpy.MakeFeatureLayer_management(in_fc, "small_islands_temp")

arcpy.SelectLayerByAttribute_management(
    "small_islands_temp",
    "NEW_SELECTION",
    "SHAPE_Area < 300"
)

arcpy.CopyFeatures_management(
    "small_islands_temp",
    "small_islands_300m"
)

count = int(arcpy.GetCount_management("small_islands_300m")[0])
print(f"Total 'Small Island' (<300 square-meters): {count}")


#===============================
#Hole Detection Post-Processing
#===============================
#structure for script adapted from GIS Stack Exchange post: https://gis.stackexchange.com/questions/27255/how-to-identify-feature-vertices-that-are-part-of-a-donut-hole-in-arcgis-10
#overwriting ouput to allow for multiple runs of this code without having to manually delete the output feature class each time
#create new gdb called scratch to hold the output "holes" feature class
#search cursor to loop through each feature in the input feature class and access its geometry
#create insert cursor to create new feature class of holes
#create for loop to itterate through each 'part' (each part is an array of points) of the geometry
#store rings in a list; reset the current ring being processed for each new part
#split rings using None separator (where None means the end of the ring); if there is a None, add the current ring to the list of rings and reset the current ring
#using append to first append points to the current ring until None is reached, then append the current ring to the list of rings and reset the current ring; ends the for loop if loop ends without None being reached and appends the current ring to the list of rings
#if 'rings' has more than one ring, there are holes to be indexed
#loop through the list of rings starting with the second ring (the first ring is the outer polygon boundary and not a hole)
#convert the array of points for the hole into a polygon geometry with the same spatial reference as the original geometry
#inserts new row into the holes feature class with the geometry of the hole
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/create-feature-class.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/describe.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/polygon.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/array.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/searchcursor-class.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/insertcursor-class.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/geometry.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/reading-geometries.htm
#resource for functions: https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/using-environment-settings.htm
arcpy.env.overwriteOutput = True

hole_fc = arcpy.CreateFeatureclass_management(
    arcpy.env.scratchGDB,
    "holes",
    "POLYGON",
    spatial_reference=arcpy.Describe(in_fc).spatialReference
)

with arcpy.da.SearchCursor(in_fc, ["OID@", "SHAPE@"]) as cursor: #using @ token to access the ID and geometry of the feature
    with arcpy.da.InsertCursor(hole_fc, ["SHAPE@"]) as insert_cursor:

        for oid, geom in cursor:
            for part in geom:  #each part is an Array

                ring = [] #current ring being processed; reset for each new part
                rings = [] #list of all rings in the current part 

                #Split rings using None separator
                for pnt in part: #points in the array of the part; None means the end of the ring
                    if pnt:
                        ring.append(pnt)
                    else: #where None is encountered, add the current ring to the list of rings and reset the current ring
                        if ring:
                            rings.append(arcpy.Array(ring))
                            ring = []

                if ring:
                    rings.append(arcpy.Array(ring)) #ends the for loop if loop ends without None being reached and appends the current ring to the list of rings

                #First ring = outer, rest = holes
                if len(rings) > 1: #if more than one ring, there are holes to be indexed
                    for hole_array in rings[1:]: #loop through the list of rings starting with the second ring (the first ring is the outer polygon boundary and not a hole)
                        hole_geom = arcpy.Polygon(
                            hole_array,
                            geom.spatialReference #convert the array of points for the hole into a polygon geometry with the same spatial reference as the original geometry
                        )
                        insert_cursor.insertRow([hole_geom]) #inserts new row into the holes feature class with the geometry of the hole
#Make feature layer here because certain python functions require a feature layer as input; this creates a feature layer from the holes feature class if needed for further processing
arcpy.MakeFeatureLayer_management(hole_fc, "hole_layer") #creates a feature layer from the holes feature class if needed for further processing (selection, etc.)

count = int(arcpy.GetCount_management(hole_fc)[0])
print(f"Total 'Holes': {count}")

print("Finished.")







