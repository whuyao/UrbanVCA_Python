UrabnVCA-Python
===============
# Overview

This project is the Python version of UrbanVCA.

UrbanVCA is a GeoAI-based software for the simulation and prediction of urban development and land-use change process by using vector-based cellular automata. UrbanVCA supports the simulation and prediction of both land use interchange and urban land use expansion processes within the city.

This project implements three data preprocessing functions (namely land use reclassification function, vector dynamic land use parcel splitting function, and land use data matching function), overall development probability calculation function, and UrbanVCA model simulation function.

This project is based on gdal.

# Operation Process
```
The order in which the program runs:
preparation
    reclassification
    DLPS
    match
    zonal
mining_Pg_RF 
simulation
```
# Module Description
## 1.land use reclassification function

Utilize the preparation_reclassification.py program for land use reclassification. 

This module allows for the transformation of values in a reclassification field to new values based on a reclassification dictionary and writing them into a new field. 

Users are required to set various parameters in the main function. 

The input_file_name and output_file_name parameters represent the file path of the land use type file (.shp) and the output path of the result file, respectively. 

The reclass_field_name parameter denotes the field name representing land use types in the land use type file.

The new_field_name parameter specifies the field name for the new land use types after reclassification. 

The reclass_dict parameter is a reclassification dictionary, where the keys represent the original land use types to be reclassified, and the values represent the new land use types after reclassification.

## 2.vector dynamic land use parcel splitting function

Utilize the preparation_DLPS.py program for vector dynamic parcel splitting. 

This module allows for parcel segmentation based on the Minimum Area Bounding Rectangle (MABR) of the parcel's convex hull. 

Users are required to set various parameters in the main function. 

The input_file_name and output_file_name parameters represent the file path of the land use types file (.shp) after land use reclassification and the output path of the result file, respectively. 

The max_iteration parameter specifies the number of segmentation iterations.

the allowable_parameter represents the allowable parameter for the segmentation process.

## 3.land use data matching function

Utilize preparation_match.py program for land use data matching. 

This module can identify the closest parcels between two different time periods and consider them as the same parcel, matching the land use types between the earlier and later periods. 

Users are required to set various parameters in the main function. 

The before_file_name parameter represents the file path of the land use types file after vector dynamic parcel splitting for the earlier period. 

The before_landuse_field_name parameter denotes the field name in the earlier period land use types file that indicates the land use type. 

The after_file_name parameter represents the file path of the land use types file after vector dynamic parcel splitting for the later period. 

The after_landuse_field_name parameter specifies the field name in the later period land use types file that represents the land use type. 

The output_file_name parameter denotes the output path for the result file.

## 4.overall development probability calculation function

Utilize preparation_zonal.py and mining_Pg_RF.py to implement the overall development probability calculation function.

preparation_zonal.py is used for zonal statistics, calculating statistical values (mean, maximum, minimum) of the pixels covered by the parcels.

Users are required to set various parameters in the main function. 

The polygon_file_name parameter represents the address of the matched land use type shapefile. 

The raster_file_config_list parameter is a list of configurations for multiple TIFF images. For each image, the first item is the image address, the second item is the field name of the spatial variable, and the third item is the method of pixel statistics.

The output_csvfile_name parameter denotes the address of the CSV result file. 

The output_shapefile_name parameter represents the output address of the shapefile result file.




mining_Pg_RF.py can utilize the Random Forest algorithm to calculate the overall development probability by using parcels as samples, the zonal statistical values of parcels on various spatial variables as features, and the later land use types as labels.

Users are required to set various parameters in the main function. 

The input_file_name parameter represents the address of the zonal statistics shapefile. 

The output_shapefile_name parameter denotes the output address of the shapefile result file. 

The output_csvfile_name parameter represents the output address of the CSV result file. 

The label_field_name parameter is the field name of the later land use types. 

The spatial_variable_field_name_list is a list of field names for various spatial variables. 

The tree_count parameter specifies the number of decision trees in the Random Forest.
## 5.UrbanVCA model simulation function

Utilize simulation.py program to implement land use simulation functionality. 

This module utilizes the UrbanVCA model to simulate the land use types from the earlier period and evaluates the simulation accuracy （Figures of Merit (FoM), User's Accuracy (UA), and Producer's Accuracy (PA)）by comparing with the actual land use types from the later period.

Users are required to set various parameters in the main function. 

The input_file_name parameter represents the address of the land use types shapefile after overall development probability calculation. 

The restricted_area_file_name parameter denotes the address of the restricted area shapefile. 

The output_file_name parameter represents the output address of the result file. 

The before_landuse_field_name parameter is the field name of the land use types from the earlier period. 

The after_landuse_field_name parameter is the field name of the land use types from the later period. 

The RA_alpha parameter is used for calculating the random factor. 

The buffer_range parameter specifies the neighborhood range. 

The iteration parameter indicates the number of iterations. 

The change parameter is the conversion matrix, where users can manually set the conversion relationships between land use types. 
If the value in the n row and m column of the matrix is 1, it means type n can be converted to type m; if it is 0, then it cannot be converted.
## 6.Other modules

assessment_FoM.py is used for accuracy assessment and can calculate the Figures of Merit (FoM), User's Accuracy (UA), and Producer's Accuracy (PA).

utils.py is used to store commonly used functions.

# Dependency libraries
* Python-3.8
* gdal-3.4.3
* numpy-1.24.3
* sklearn-0.0.post10

# Data specification
```
In the data folder: 
2015.shp and 2018.shp are land use type test data for two different years; 
restrictedArea.shp is the area where development is restricted in the final simulation step;
Other Tiff files are spatial auxiliary variables used in calculating the overall development probability.
```

# Reference

[1] Yao, Y., Liu, X., Li, X., Liu, P., Hong, Y., Zhang, Y., & Mai, K. (2017). Simulating urban land-use changes at a large scale by integrating dynamic land parcel subdivision and vector-based cellular automata. International Journal of Geographical Information Science, 31(12), 2452-2479.

[2] Zhai, Y., Yao, Y., Guan, Q., Liang, X., Li, X., Pan, Y., … & Zhou, J. (2020). Simulating urban land use change by integrating a convolutional neural network with vector-based cellular automata. International Journal of Geographical Information Science, 34(7), 1475-1499.

[3] Yao, Y., Li, L., Liang, Z., Cheng, T., Sun, Z., Luo, P., … & Ye, X. (2021). UrbanVCA: a vector-based cellular automata framework to simulate the urban land-use change at the land-parcel level. arXiv preprint arXiv:2103.08538.








