from osgeo import ogr
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import Driver
from osgeo.ogr import Geometry

import numpy as np
from numpy import ndarray

def copy_shapefile(source_file_name:str,output_file_name:str) -> None:
    '''
    ### Abstract
        Copy the shapefile file
    ### Parameters
        - source_file_name：The original file to be copied
        - output_file_name：Output file

    ### Return
        none
    '''
    source_file:DataSource=ogr.Open(source_file_name)
    driver:Driver = ogr.GetDriverByName("ESRI Shapefile")
    driver.CopyDataSource(source_file,output_file_name)
    return

def get_feature_list(file_name:str)->list:
    '''
    ### Abstract
        Copy all the elements in the shapefile
    ### Parameters
        - file_name：The name of the shapefile to be copied

    ### Return
        A list of components
    '''
    file:DataSource=ogr.Open(file_name)
    layer:Layer=file.GetLayer()
    feature_list=[]

    feature:Feature
    for feature in layer:
        feature_list.append(feature.Clone())

    file=None
    return feature_list

def apart_multipolygon(feature_list:list)->list:
    '''
    ### Abstract
        Convert multipolygon to polygon
    ### Parameters
        - feature_list：List of parcels

    ### Return
        List of parcels
    '''
    multipolygon_index=[]
    new_feature_list=[]
    feature:Feature
    for index,feature in enumerate(feature_list):
        geometry:Geometry=feature.GetGeometryRef()
        geometry_name=geometry.GetGeometryName()

        if geometry_name=="MULTIPOLYGON":
            multipolygon_index.append(index)
            polygon_count=geometry.GetGeometryCount()
            for i in range(polygon_count):
                new_feature:Feature=feature.Clone()
                new_geometry:Geometry=geometry.GetGeometryRef(i)
                new_feature.SetGeometry(new_geometry)
                new_feature_list.append(new_feature)

    multipolygon_index.reverse()
    for index in multipolygon_index:
        feature_list.pop(index)
    
    return feature_list+new_feature_list

def delete_all_feature(layer:Layer)->None:
    '''
    ### Abstract
        Delete all elements from the layer
    ### Parameters
        - layer：The layer you want to remove the element from

    ### Return
        none
    '''
    feature_count=layer.GetFeatureCount()
    for FID in range(feature_count-1,-1,-1):
        layer.DeleteFeature(FID)

def add_all_feature(layer:Layer,feature_list:list)->None:
    '''
    ### Abstract
        Copy the elements from the elements list to the layer
    ### Parameters
        - layer：layer
        - feature_list：Element list

    ### Return
        none
    '''
    for feature in feature_list:
        layer.CreateFeature(feature)

def get_centroids(feature_list: list) -> ndarray:
    '''
    ### Abstract
        Get the centroid points of all the parcels
    ### Parameters
        - feature_list：List of parcels

    ### Return
        centroids[i],which represents the centroid point coordinates of block i
    '''
    centroids = np.zeros(shape=(len(feature_list), 2))

    feature: Feature
    for index, feature in enumerate(feature_list):
        geometry: Geometry = feature.GetGeometryRef()
        centroid: Geometry = geometry.Centroid()
        centroids[index] = centroid.GetPoint_2D()

    return centroids

def get_distance_matrix(before_feature_list: list, after_feature_list: list) -> ndarray:
    '''

    ### Abstract
        Calculate the distance between each of the two parcel lists
    ### Parameters
        - before_feature_list：List of previous parcels
        - after_feature_list：List of later parcels

    ### Return
        distance_matrix[i,j] represents the distance between the I-th block in the earlier period and the J-th block in the later period

    '''

    before_feature_count = len(before_feature_list)
    after_feature_count = len(after_feature_list)
    distance_matrix = np.zeros(shape=(before_feature_count, after_feature_count))

    before_centroids = get_centroids(before_feature_list)
    after_centroids = get_centroids(after_feature_list)

    for before_index, before_centroid in enumerate(before_centroids):
        for after_index, after_centroid in enumerate(after_centroids):
            distance_matrix[before_index, after_index] = np.linalg.norm(before_centroid-after_centroid)
            print(before_index," ",after_index)

    return distance_matrix

