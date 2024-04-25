from osgeo import ogr
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import FieldDefn
from osgeo.ogr import Geometry
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt
import secrets
from utils import copy_shapefile
from utils import get_feature_list
from utils import get_distance_matrix
import random
from assessment_FoM import assessment_FoM
import os
os.environ['PROJ_LIB'] = r'C:\Users\dell\AppData\Local\Programs\Python\Python38\Lib\site-packages\osgeo\data\proj'
def get_landuse_type_list(feature_list:list,landuse_field_name:str)->list:
    '''
    ### Abstract
        Get all values for the land use field, then remove the same values
    ### Parameters
        - feature_list: parcels list
        - landuse_field_name: The field name of the land use

    ### Return
        List of land use types
    '''
    landuse_type_list=[]
    feature:Feature
    for feature in feature_list:
        landuse_type_list.append(feature.GetField(landuse_field_name))

    return list(set(landuse_type_list))

def get_RA(parcel_count:int,alpha:float)->ndarray:
    '''
    ### Abstract
        Calculate the random factors for each parcel
    ### Parameters
        - parcel_count：Number of parcels
        - alpha：Random factor calculation parameters

    ### Return
        RA[i] represents the random factor of parcel i
    '''
    gama=np.random.random(size=(parcel_count,))
    RA=np.power(-np.log(gama),alpha)+1
    
    return RA

def get_Pc(feature_list:list,restricted_feature_list:list)->ndarray:
    '''
    ### Abstract
        Calculate whether each parcel intersects the restricted area, where Pc is 0 and otherwise 1
    ### Parameters
        - feature_list：parcels list
        - restricted_feature_list：Restricted area list

    ### Return
        Pc[i] indicates the Pc value of parcel i
    '''
    Pc=np.zeros(shape=(len(feature_list),))

    feature:Feature
    restricted_feature:Feature
    for index,feature in enumerate(feature_list):
        for restricted_feature in restricted_feature_list:
            geometry:Geometry=feature.GetGeometryRef()
            if geometry.Intersects(restricted_feature.GetGeometryRef()):
                Pc[index]=0
            else:
                Pc[index]=1

    return Pc

def get_areas_and_areamax_and_areamin(feature_list:list)->tuple:
    '''
    ### Abstract
        Obtain the area of all parcels, as well as their maximum and minimum values
    ### Parameters
        - feature_list：parcels list

    ### Return
        parcel area, maximum area, minimum area
    '''
    areas=np.zeros(shape=(len(feature_list),))

    feature:Feature
    for index,feature in enumerate(feature_list):
        geometry:Geometry=feature.GetGeometryRef()
        areas[index]=geometry.GetArea()
    
    return (areas,areas.max(),areas.min())

def get_omega(current_landuse_list:list,landuse_type_list:list,buffer_range:float,distance_matrix:ndarray,areas:ndarray,areamax:float,areamin:float)->ndarray:
    '''
    ### Abstract
        Calculate the neighborhood effect of each parcel on each land type.
    ### Parameters
        - current_landuse_list：List of current land use types for each parcel
        - landuse_type_list：List of land use types
        - buffer_range：Neighborhood distance
        - distance_matrix：The distance between two parcels
        - areas：areas of all parcels
        - areamax：Maximum area of all plots
        - areamin：Minimum area of all plots

    ### Return
        omega[i,j] indicates that plot i is subject to the neighborhood effect of plots of land use type j
    '''
    landuse_count=len(current_landuse_list)
    omega=np.zeros(shape=(landuse_count,len(landuse_type_list)))
    
    for index_i in range(landuse_count):
        for index_j in range(landuse_count):
            distance_ij=distance_matrix[index_i,index_j]
            if distance_ij<=buffer_range:
                landuse_type=current_landuse_list[index_j]
                landuse_type_index=landuse_type_list.index(landuse_type)

                omega[index_i,landuse_type_index]+=np.power(np.e,-distance_ij/buffer_range)*((areas[index_j]/areas[index_i])/(areamax/areamin))
  
    return omega

def get_Pg(feature_list:list,pg_field_name_list:list)->ndarray:
    '''
    ### Abstract
        Read pg from the parcels
    ### Parameters
        - feature_list：parcels list
        - pg_field_name_list：pg field name for each land use type

    ### Return
        The pg array of each parcel has the shape of m rows and n columns, m is the number of plots, n is the number of land use types
    '''
    Pg=np.zeros(shape=(len(feature_list),len(pg_field_name_list)))

    feature:Feature
    for feature_index,feature in enumerate(feature_list):
        for pg_field_name_index,pg_field_name in enumerate(pg_field_name_list):
            Pg[feature_index,pg_field_name_index]=feature.GetField(pg_field_name)
    
    return Pg

def get_pg_field_name_list(landuse_type_list:list)->list:
    '''
    ### Abstract
       Adding 'pg_' to the name of the land use type is the corresponding pg field name
    ### Parameters
        - landuse_type_list：List of land use types

    ### Return
        pg field name for each land use type
    '''
    pg_field_name_list=[]
    for landuse_type in landuse_type_list:
        pg_field_name_list.append('pg_'+landuse_type)

    return pg_field_name_list

def filter_error_value(feature_list:list,pg_field_name_list:list,error_value:float)->tuple:
    '''
    ### Abstract
        Remove parcels containing error values in the pg field
    ### Parameters
        - feature_list：parcels list
        - pg_field_name_list：A list of each pg field name
        - error_value：Error value

    ### Return
        FID of the filtered plots and list of plots
    '''
    error_feature_FID_list=[]
    nonerror_feature_FID_list=[]

    feature:Feature
    for FID,feature in enumerate(feature_list):
        is_error=False
        for pg_field_name in pg_field_name_list:
            value=feature.GetField(pg_field_name)
            if value==error_value:
                is_error=True
                error_feature_FID_list.append(FID)
                break
        if is_error==False:
            nonerror_feature_FID_list.append(FID)

    error_feature_FID_list.reverse()
    for error_feature_FID in error_feature_FID_list:
        feature_list.pop(error_feature_FID)
    
    return (nonerror_feature_FID_list,feature_list)
        

def get_area_change_matrix(areas:ndarray,before_landuse_list:list,after_landuse_list:list,landuse_type_list:list)->ndarray:
    '''
    ### Abstract
        The land area conversion matrix of each land use type is calculated, and the land with unchanged type is ignored
    ### Parameters
        - areas：Area of parcels
        - before_landuse_list：Previous land use list of the parcel
        - after_landuse_list：Later land use list of parcel
        - landuse_type_list：List of land use types

    ### Return
        area_change_matrix, area_change_matrix[i,j] represents the area of land use type i transformed into land use type j
    '''
    landuse_type_count=len(landuse_type_list)
    area_change_matrix=np.zeros(shape=(landuse_type_count,landuse_type_count))

    for index,before_landuse in enumerate(before_landuse_list):
        after_landuse=after_landuse_list[index]

        before_landuse_index=landuse_type_list.index(before_landuse)
        after_landuse_index=landuse_type_list.index(after_landuse)

        if before_landuse_index==after_landuse_index:
            continue
        area_change_matrix[before_landuse_index,after_landuse_index]+=areas[index]

    return area_change_matrix

def get_before_and_after_landuse_list(feature_list:list,before_landuse_field_name:str,after_landuse_field_name:str)->tuple:
    '''
    ### Abstract
        To get the land use type in the early and late period
    ### Parameters
        - feature_list：parcels list
        - before_landuse_field_name：The name of a field that represents previous land use
        - after_landuse_field_name：The name of a field that represents late land use

    ### Return
        List of land use in the early stage and list of land use in the later stage
    '''
    before_landuse_list=[]
    after_landuse_list=[]
    
    feature:Feature
    for feature in feature_list:
        before_landuse_list.append(feature.GetField(before_landuse_field_name))
        after_landuse_list.append(feature.GetField(after_landuse_field_name))

    return before_landuse_list,after_landuse_list

def iteration_once(Pg:ndarray,omega:ndarray,Pc:ndarray,RA:ndarray,landuse_type_list:list,current_landuse_list:list,areas:ndarray,area_change_matrix:ndarray,change:ndarray)->tuple:
    '''
    ### Abstract
        The cellular automata iterates once
    ### Parameters
        - Pg：overall development probability
        - omega：Neighborhood effect
        - Pc：Limiting factor
        - RA：Random factor
        - landuse_type_list：List of land use types
        - current_landuse_list：Current land use types of each area
        - areas：Area of parcels
        - area_change_matrix：Land area transformation matrix of each land use type

    ### Return
        The land use type of each area after iteration and the area transformation matrix after iteration
    '''
    P=np.zeros(shape=Pg.shape)
    area_change_matrix_copy = area_change_matrix.copy()
    feature_count=Pg.shape[0]
    for i in range(feature_count):
        P[i]=Pg[i]*omega[i]*Pc[i]*RA[i]

    #feature_indices=np.random.randint(0,feature_count,size=(10,))

    index=np.arange(len(landuse_type_list))
    for feature_index in range(feature_count):
        feature_indices = secrets.randbelow(feature_count)
        Pi=P[feature_indices]

        if Pi.sum()==0:
            continue
        current_landuse=current_landuse_list[feature_indices]
        count=0
        current_landuse_index = landuse_type_list.index(current_landuse)
        while(1):
            change_landuse=landuse_type_list[np.random.choice(index,p=Pi/Pi.sum())]
            count+=1
            if(change[current_landuse_index][current_landuse_index]==1):
                break
            if(count>5):
                change_landuse=current_landuse
                break
        # change_landuse=landuse_type_list[Pi.argmax()]

        change_landuse_index=landuse_type_list.index(change_landuse)

        area=areas[feature_indices]
        if area_change_matrix_copy[current_landuse_index,change_landuse_index]-area<0:
            continue
        area_change_matrix_copy[current_landuse_index,change_landuse_index]-=area
        current_landuse_list[feature_indices]=change_landuse

    # Pi:ndarray
    # for i,Pi in enumerate(P):
    #     current_landuse=current_landuse_list[i]
    #     change_landuse=landuse_type_list[Pi.argmax()]

    #     current_landuse_index=landuse_type_list.index(current_landuse)
    #     change_landuse_index=landuse_type_list.index(change_landuse)

    #     area=areas[i]
    #     if area_change_matrix[current_landuse_index,change_landuse_index]-area<0:
    #         continue
    #     area_change_matrix[current_landuse_index,change_landuse_index]-=area
    #     current_landuse_list[i]=change_landuse

    return current_landuse_list,area_change_matrix

def get_current_landuse_list(feature_list:list,landuse_field_name:str)->list:
    '''
    ### Abstract
        Get the current land use of various blocks
    ### Parameters
        - feature_list：parcels list
        - landuse_field_name：The field name of the land use

    ### Return
        Current land use of each blocks
    '''
    current_landuse_list=[]

    feature:Feature
    for feature in feature_list:
        current_landuse_list.append(feature.GetField(landuse_field_name))

    return current_landuse_list

def write_to_file(output_file_name:str,current_landuse_list:list,FID:list,error_value:float)->None:
    '''
    ### Abstract
        Write simulation results to the shapefile file
    ### Parameters
        - output_file_name：Output file name
        - current_landuse_list：List of land use simulation results
        - FID：A list of Fids for each block
        - error_value：Error value

    ### Return
        none
    '''
    file: DataSource = ogr.Open(output_file_name,1)
    layer:Layer = file.GetLayer()

    field_defn:FieldDefn=FieldDefn('simulated',ogr.OFTString)
    layer.CreateField(field_defn)

    feature:Feature
    for feature in layer:
        feature.SetField('simulated',str(error_value))
        layer.SetFeature(feature)

    for index,fid in enumerate(FID):
        feature=layer.GetFeature(fid)
        feature.SetField('simulated',str(current_landuse_list[index]))
        layer.SetFeature(feature)


def simulation(input_file_name:str,restricted_area_file_name:str,output_file_name:str,before_landuse_field_name:str,after_landuse_field_name:str,RA_alpha:float,buffer_range:float,iteration:int,error_value:float=-99999,change=[[] * 5] ):
    '''
    ### Abstract
        Land use simulation
    ### Parameters
        - input_file_name：The address of the land use types shapefile after overall development probability calculation
        - restricted_area_file_name：The address of the restricted area shapefile
        - output_file_name：The output address of the result file
        - before_landuse_field_name：The field name of the land use types from the earlier period
        - after_landuse_field_name：The field name of the land use types from the later period.
        - RA_alpha：Calculating the random factor
        - buffer_range：The neighborhood range
        - iteration：The number of iterations
        - change：The conversion matrix.If the value in the n row and m column of the matrix is 1, it means type n can be converted to type m; if it is 0, then it cannot be converted

    ### Return
        none
    '''
    copy_shapefile(input_file_name,output_file_name)


    restricted_feature_list=get_feature_list(restricted_area_file_name)
    feature_list=get_feature_list(output_file_name)


    landuse_type_list=get_landuse_type_list(feature_list,before_landuse_field_name)
    pg_field_name_list=get_pg_field_name_list(landuse_type_list)


    FID,feature_list=filter_error_value(feature_list,pg_field_name_list,error_value)

    areas,areamax,areamin=get_areas_and_areamax_and_areamin(feature_list)
    before_landuse_list,after_landuse_list=get_before_and_after_landuse_list(feature_list,before_landuse_field_name,after_landuse_field_name)
    area_change_matrix=get_area_change_matrix(areas,before_landuse_list,after_landuse_list,landuse_type_list)
    current_landuse_list=get_current_landuse_list(feature_list,before_landuse_field_name)
    distance_matrix=get_distance_matrix(feature_list,feature_list)

    Pg=get_Pg(feature_list,pg_field_name_list)
    Pc=get_Pc(feature_list,restricted_feature_list)
    area_change_matrix = area_change_matrix/iteration
    for i in range(iteration):
        RA=get_RA(len(feature_list),RA_alpha)
        omega=get_omega(current_landuse_list,landuse_type_list,buffer_range,distance_matrix,areas,areamax,areamin)

        current_landuse_list,area_change_matrix=iteration_once(Pg,omega,Pc,RA,landuse_type_list,current_landuse_list,areas,area_change_matrix,change)

        print(i,assessment_FoM(before_landuse_list,after_landuse_list,current_landuse_list,areas))

    write_to_file(output_file_name,current_landuse_list,FID,error_value)

if __name__=='__main__':
    simulation(
        input_file_name=r"E:\UrbanVCA_Python\output\pg.shp",
        restricted_area_file_name=r"E:\UrbanVCA_Python\data\restrictedArea.shp",
        output_file_name=r"E:\UrbanVCA_Python\output\simulated.shp",
        before_landuse_field_name='before',
        after_landuse_field_name='after',
        RA_alpha=5,
        buffer_range=600,
        iteration=5,
        change=[[1,0,1,1,1],
                [1,1,1,1,1],
                [1,0,1,1,1],
                [1,0,1,1,1],
                [1,0,1,1,1],
                ]
    )