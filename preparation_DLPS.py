from osgeo import ogr
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import Geometry
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt
import random
from utils import copy_shapefile
from utils import get_feature_list
from utils import apart_multipolygon
from utils import delete_all_feature
from utils import add_all_feature
import os
os.environ['PROJ_LIB'] = r'C:\Users\dell\AppData\Local\Programs\Python\Python38\Lib\site-packages\osgeo\data\proj'
def get_radian_with_x_axis(vector: ndarray) -> float:
    '''
    ### Abstract
        Calculate the radian of the Angle between the vector and the X-axis. If the vector is in the first and second quadrants, the rotation Angle is negative so that the convex envelope rotates clockwise
    ### Parameters
        - vector：The vector of radians to be calculated with the X-axis

    ### Return
        The arc of the Angle
    '''
    x_axis = np.array([1, 0])
    cos = np.dot(vector/np.linalg.norm(vector), x_axis/np.linalg.norm(x_axis))
    radian = np.arccos(cos)
    if vector[1] > 0:
        radian = -radian
    return radian


def get_rotated_points(anchor: ndarray, points: ndarray, radian: float) -> ndarray:
    '''
    ### Abstract
        Rotate all points counterclockwise around a point
    ### Parameters
        - anchor：Rotate around that point
        - points：The set of points to rotate
        - radian：The radian of the rotation Angle

    ### Return
        The set of points after rotation
    '''
    rotate_matrix = np.array([[np.cos(radian), np.sin(radian)],
                              [-np.sin(radian), np.cos(radian)]])
    return (points-anchor).dot(rotate_matrix)+anchor


def get_rectangle(points: ndarray) -> ndarray:
    '''
    ### Abstract
        Find the minimum and maximum values of the x and y coordinates of all points, resulting in an external rectangle
    ### Parameters
        - points：The set of points of the surrounding rectangle will be evaluated

    ### Return
        The set of points that make up the external rectangle
    '''
    xmin = points[:, 0].min()
    xmax = points[:, 0].max()
    ymin = points[:, 1].min()
    ymax = points[:, 1].max()

    return np.array([[xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin], [xmin, ymax]])


def get_rectangle_area(rectangle_points: ndarray) -> float:
    '''
    ### Abstract
        Calculate the area of a rectangle with sides parallel to the x and y axes
    ### Parameters
        - The set of points that make up a rectangle

    ### Return
        Rectangular area
    '''
    dx = rectangle_points[1, 0]-rectangle_points[0, 0]
    dy = rectangle_points[0, 1]-rectangle_points[2, 1]
    return dx*dy


def get_long_edge_index(MABR: ndarray) -> int:
    '''
    ### Abstract
        Calculate the length of the two adjacent sides and get the index of the points that make up the long sides
    ### Parameters
        - MABR：The set of points that make up MABR

    ### Return
        If the edge of the 0 and 1 points is the long side, 1 is returned
        If the edge of points 0 and 3 is the long side, then 3 is returned
    '''
    distance_0_1 = np.linalg.norm(MABR[0]-MABR[1])
    distance_0_3 = np.linalg.norm(MABR[0]-MABR[3])

    if distance_0_1 > distance_0_3:
        return 1
    return 3


def get_bisected_MABR(MABR: ndarray) -> ndarray:
    '''
    ### Abstract
        Bisect the long sides of the MABR, resulting in two rectangles
    ### Parameters
        - MABR：The set of points that make up MABR

    ### Return
        An array of two small rectangles of the shape 2x5x2, two rectangles with five points each, and xy two values at each point
    '''

    bisected_MABR = np.zeros(shape=(2, 5, 2))

    long_edge_index = get_long_edge_index(MABR)
    if long_edge_index == 1:
        midpoint_0_1 = (MABR[0]+MABR[1])/2
        midpoint_2_3 = (MABR[2]+MABR[3])/2

        bisected_MABR[0, 0] = MABR[0]          # 0-------------1
        bisected_MABR[0, 1] = midpoint_0_1     # |      |      |
        bisected_MABR[0, 2] = midpoint_2_3     # |      |      |
        bisected_MABR[0, 3] = MABR[3]          # |      |      |
        bisected_MABR[0, 4] = MABR[0]          # 3-------------2

        bisected_MABR[1, 0] = midpoint_0_1
        bisected_MABR[1, 1] = MABR[1]
        bisected_MABR[1, 2] = MABR[2]
        bisected_MABR[1, 3] = midpoint_2_3
        bisected_MABR[1, 4] = midpoint_0_1

    if long_edge_index == 3:
        midpoint_0_3 = (MABR[0]+MABR[3])/2
        midpoint_1_2 = (MABR[1]+MABR[2])/2

        bisected_MABR[0, 0] = MABR[0]          # 0-------------1
        bisected_MABR[0, 1] = MABR[1]          # |             |
        bisected_MABR[0, 2] = midpoint_1_2     # |             |
        bisected_MABR[0, 3] = midpoint_0_3     # |             |
        bisected_MABR[0, 4] = MABR[0]          # |             |
                                               # |-------------|
        bisected_MABR[1, 0] = midpoint_0_3     # |             |
        bisected_MABR[1, 1] = midpoint_1_2     # |             |
        bisected_MABR[1, 2] = MABR[2]          # |             |
        bisected_MABR[1, 3] = MABR[3]          # |             |
        bisected_MABR[1, 4] = midpoint_0_3     # 3-------------2
    return bisected_MABR


def get_MABR(convex_hull_points: ndarray) -> ndarray:
    '''
    ### Abstract
        According to the theorem of geometry, one of the MABR edges of the convex hull coincides with one of the edges of the convex hull
        Therefore, the MABR corresponding to all sides of the convex hull is obtained, and the MABR with the smallest area is returned
    ### Parameters
        - convex_hull_points：Point sequence of convex hull

    ### Return
        The outer rectangle with the smallest area, which is MABR
    '''
    edge_count: int = len(convex_hull_points)-1
    # Each edge of the convex hull corresponds to the area of an external rectangle
    areas: ndarray = np.zeros(shape=(edge_count,))
    rectangle_list: list = []

    # Traverse each side of the convex hull
    for i in range(edge_count):
        # The Angle between the current side and the X-axis
        radian = get_radian_with_x_axis(convex_hull_points[i]-convex_hull_points[i+1])
        # Rotate the convex hull around one end of the current edge so that the current edge is parallel to the X-axis
        rotated_points = get_rotated_points(convex_hull_points[i], convex_hull_points, radian)
        # The external rectangle of the convex hull after rotation
        rectangle = get_rectangle(rotated_points)
        # Calculate the area of the outer rectangle
        areas[i] = get_rectangle_area(rectangle)
        # The outer rectangle is rotated in reverse to obtain the outer rectangle that covers the convex hull before rotation
        rectangle = get_rotated_points(convex_hull_points[i], rectangle, -radian)
        # Adds the external rectangle to the candidate list
        rectangle_list.append(rectangle)

    # Returns the external rectangle with the smallest area
    return rectangle_list[areas.argmin()]

def write_to_file(output_file_name:str,feature_list:list)->None:
    '''
    ### Abstract
        All plots are emptied and written into new plots
    ### Parameters
        - output_file_name：The file name of the plots to be written
        - feature_list：A list of all the plots to be written consists of

    ### Return
        none
    '''
    file: DataSource = ogr.Open(output_file_name,1)
    layer:Layer = file.GetLayer()
    delete_all_feature(layer)
    add_all_feature(layer,feature_list)

def get_mean_and_std_of_area(feature_list:list)->tuple:
    '''
    ### Abstract
        The mean and standard deviation of all plots were obtained
    ### Parameters
        - feature_list：List of all plots composed

    ### Return
        A tuple of mean and standard deviation
    '''
    areas=np.zeros(shape=(len(feature_list),))
    feature:Feature
    for index,feature in enumerate(feature_list):
        geometry:Geometry=feature.GetGeometryRef()
        areas[index]=geometry.GetArea()

    return (areas.mean(),areas.std())

def points_to_polygon(points:ndarray)->Geometry:
    '''
    ### Abstract
        Convert the sequence of points to polygon for GDAL processing
    ### Parameters
        - points：Sequence of points, shape n rows 2 columns, n is the number of points, the two columns are respectively the xy coordinates of points, the first point and the last point must be the same

    ### Return
        polygon with a sequence of points entered
    '''
    ring:Geometry=Geometry(ogr.wkbLinearRing)
    for point in points:
        ring.AddPoint(point[0],point[1])
    polygon:Geometry=Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    
    return polygon

def split_feature_into_two(feature:Feature)->tuple:
    '''
    ### Abstract
        Divide a plot. Firstly, the convex hull of the block is obtained, and then MABR is obtained. The MABR is divided into two parts and intersected with the block to obtain the divided block
    ### Parameters
        - feature：A plot to be divided

    ### Return
        A tuple of two new blocks
    '''
    geometry:Geometry=feature.GetGeometryRef()
    convex_hull:Geometry=geometry.ConvexHull()

    MABR=get_MABR(np.array(convex_hull.GetGeometryRef(0).GetPoints())[:,:2])
    bisected_MABR=get_bisected_MABR(MABR)

    polygon1=points_to_polygon(bisected_MABR[0])
    polygon2=points_to_polygon(bisected_MABR[1])

    new_feature1:Feature=feature.Clone()
    new_feature1.SetGeometry(geometry.Intersection(polygon1))
    new_feature2:Feature=feature.Clone()
    new_feature2.SetGeometry(geometry.Intersection(polygon2))

    return (new_feature1,new_feature2)

def split_once(feature_list:list,allowable_parameter:float)->list:
    '''
    ### Abstract
        The mean and standard deviation of all plots were obtained, the plots that met the requirements of segmentation were divided, two new plots were obtained, and the old plots that had been divided were deleted
    ### Parameters
        - feature_list：List of all plots
        - allowable_parameter：allowable parameter

    ### Return
        List of subdivided plots
    '''
    mean,std=get_mean_and_std_of_area(feature_list)
    
    new_feature_list=[]
    splited_feature_index=[]
    random_number = random.random()
    feature:Feature
    for index,feature in enumerate(feature_list):
        geometry:Geometry=feature.GetGeometryRef()
        area=geometry.GetArea()

        if area>mean+allowable_parameter*std*random_number:
            splited_feature_index.append(index)
            new_feature1,new_feature2=split_feature_into_two(feature)
            new_feature_list.append(new_feature1)
            new_feature_list.append(new_feature2)
            
    splited_feature_index.reverse()
    for index in splited_feature_index:
        feature_list.pop(index)

    return feature_list+new_feature_list


def DLPS(input_file_name:str,output_file_name:str,max_iteration:int,allowable_parameter:float)->None:
    '''
    ### Abstract
        parcel segmentation based on the Minimum Area Bounding Rectangle (MABR) of the parcel's convex hull
    ### Parameters
        - input_file_name: the file path of the land use types file (.shp) after land use reclassification
        - output_file_name: the output path of the result file
        - max_iteration: the number of segmentation iterations
        - allowable_parameter: the allowable parameter for the segmentation process

    ### Return
        none
    '''
    copy_shapefile(input_file_name,output_file_name)

    feature_list=get_feature_list(output_file_name)
    feature_list=apart_multipolygon(feature_list)

    for i in range(max_iteration):
        feature_list=split_once(feature_list,allowable_parameter)
        feature_list=apart_multipolygon(feature_list)

    write_to_file(output_file_name,feature_list)
    return


if __name__=='__main__':
    DLPS(
        input_file_name=r"E:\UrbanVCA_Python\output\2015_re.shp",
        output_file_name=r"E:\UrbanVCA_Python\output\2015_dlps.shp",
        max_iteration=6,
        allowable_parameter=2)

    DLPS(
        input_file_name=r"E:\UrbanVCA_Python\output\2018_re.shp",
        output_file_name=r"E:\UrbanVCA_Python\output\2018_dlps.shp",
        max_iteration=6,
        allowable_parameter=2)
