from osgeo import ogr
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import FieldDefn
from osgeo.ogr import FeatureDefn
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt
from utils import copy_shapefile
from utils import get_feature_list
from utils import apart_multipolygon
from utils import delete_all_feature
from utils import add_all_feature
from utils import get_distance_matrix
import os
os.environ['PROJ_LIB'] = r'C:\Users\dell\AppData\Local\Programs\Python\Python38\Lib\site-packages\osgeo\data\proj'

def get_change_table(before_feature_list: list, before_landuse_field_name: str, after_feature_list: list, after_landuse_field_name: str, distance_matrix: ndarray) -> list:
    '''
    ### Abstract
        In before_feature_list and after_feature_list, find the two plots that are closest to each other and view them as the same plot to get the two phases of the land use type
    ### Parameters
        - before_feature_list：List of all previous plots
        - before_landuse_field_name：The name of the field that previously represented the land use type
        - after_feature_list：List of all plots later
        - after_landuse_field_name：The name of the field that later indicates the land use type
        - distance_matrix：distance_matrix[i,j] represents the distance between the I-th block in the earlier period and the J-th block in the later period

    ### Return
        The list has n rows and two columns, n indicates the number of pre-land plots, the first is the pre-land type, the second is the post-land type
    '''
    change_table = []
    for _ in range(distance_matrix.shape[0]):
        row = []
        row.append(0)
        row.append(0)
        change_table.append(row)

    after_indices = distance_matrix.argmin(axis=1)

    for before_index, after_index in enumerate(after_indices):
        before_feature: Feature = before_feature_list[before_index]
        after_feature: Feature = after_feature_list[after_index]

        change_table[before_index][0] = before_feature.GetField(before_landuse_field_name)
        change_table[before_index][1] = after_feature.GetField(after_landuse_field_name)

    return change_table


def write_to_file(output_file_name: str, feature_list: list, change_table: ndarray) -> None:
    '''
    ### Abstract
        Write the land type of the two phases into shapefile file
    ### Parameters
        - output_file_name：The name of the shapefile file being written to
        - feature_list：List of all land uses
        - change_table：A list of all land parcels with two phase site types

    ### Return
        none
    '''
    file: DataSource = ogr.Open(output_file_name, 1)
    layer: Layer = file.GetLayer()

    delete_all_feature(layer)
    add_all_feature(layer, feature_list)


    field_defn = FieldDefn('before', ogr.OFTString)
    layer.CreateField(field_defn)
    field_defn = FieldDefn('after', ogr.OFTString)
    layer.CreateField(field_defn)


    feature: Feature
    for index, feature in enumerate(layer):
        feature.SetField('before', change_table[index][0])
        feature.SetField('after', change_table[index][1])
        layer.SetFeature(feature)


    delete_field_indices = []
    layer_defn: FeatureDefn = layer.GetLayerDefn()
    field_count = layer_defn.GetFieldCount()
    for i in range(field_count):
        field_defn: FieldDefn = layer_defn.GetFieldDefn(i)
        field_name = field_defn.GetName()
        if field_name != 'before' and field_name != 'after':
            delete_field_indices.append(i)

    delete_field_indices.reverse()
    for i in delete_field_indices:
        layer.DeleteField(i)

    return

def match(before_file_name: str,
          before_landuse_field_name: str,
          after_file_name: str,
          after_landuse_field_name: str,
          output_file_name: str) -> None:
    '''
    ### Abstract
        In the two phases, the closest land parcel is regarded as the same land parcel, and the land use type in the earlier and later phases is matched
    ### Parameters
        - before_file_name：the file path of the land use types file after vector dynamic parcel splitting for the earlier period
        - before_landuse_field_name：the field name in the earlier period land use types file that indicates the land use type
        - after_file_name：the file path of the land use types file after vector dynamic parcel splitting for the later period
        - after_landuse_field_name：the field name in the later period land use types file that represents the land use type
        - output_file_name：the output path for the result file

    ### Return
        none
    '''
    copy_shapefile(before_file_name, output_file_name)

    before_feature_list = get_feature_list(before_file_name)
    after_feature_list = get_feature_list(after_file_name)
    before_feature_list = apart_multipolygon(before_feature_list)
    after_feature_list = apart_multipolygon(after_feature_list)

    distance_matrix = get_distance_matrix(before_feature_list, after_feature_list)
    change_table = get_change_table(before_feature_list, before_landuse_field_name,after_feature_list, after_landuse_field_name, distance_matrix)

    write_to_file(output_file_name, before_feature_list, change_table)

    return

if __name__ == '__main__':
    match(
        before_file_name=r"E:\UrbanVCA_Python\output\2015_dlps.shp",
        before_landuse_field_name='new',
        after_file_name=r"E:\UrbanVCA_Python\output\2018_dlps.shp",
        after_landuse_field_name='new',
        output_file_name=r"E:\UrbanVCA_Python\output\match.shp")
