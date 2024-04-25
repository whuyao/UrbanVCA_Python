from osgeo import ogr
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import FieldDefn
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt
from utils import copy_shapefile
from utils import get_feature_list

from sklearn.ensemble import RandomForestClassifier
import os
os.environ['PROJ_LIB'] = r'C:\Users\dell\AppData\Local\Programs\Python\Python38\Lib\site-packages\osgeo\data\proj'
def encode_y(y:list)->tuple:
    '''
    ### Abstract
        Converts text labels to numeric labels for input to the model.Such as[a,b,c]->[0,1,2]
    ### Parameters
        - y：A list of text tags to convert

    ### Return
        Converted array labels, as well as a dictionary of text and number labels
    '''
    new_y=np.zeros(shape=(len(y),))

    mapping={}
    type_name_list=list(set(y))
    for index,type_name in enumerate(type_name_list):
        mapping[type_name]=index
    
    for index,yi in enumerate(y):
        new_y[index]=mapping[yi]
    
    return new_y,mapping

def make_dataset(file_name:str,label_field_name:str,spatial_variable_field_name_list:list,error_value:float)->tuple:
    '''
    ### Abstract
        The data set is extracted from the shapefile file for use by the pg mining model
    ### Parameters
        - file_name：shapefile name after partition statistics are collected
        - label_field_name：Field name denoting the type of land use in the later period
        - spatial_variable_field_name_list：A list of field names for each spatial variable
        - error_value：Error value during partition statistics

    ### Return
        FID after removing blocks with error values in the spatial variable field
        The spatial variable value of each block is shaped as n rows and m columns, n is the number of blocks, and m is the number of spatial variables
        The late land use types of each block
    '''
    feature_list=get_feature_list(file_name)

    FID=[]
    x=[]
    y=[]
    feature:Feature
    for index,feature in enumerate(feature_list):
        row=[]
        for spatial_variable_field_name in spatial_variable_field_name_list:
            value=feature.GetField(spatial_variable_field_name)
            if value==error_value:
                row=[]
                break
            row.append(value)
        if len(row)==0:
            continue
        x.append(row)
        FID.append(index)
        y.append(feature.GetField(label_field_name))

    return (np.array(FID,dtype=np.int32),np.array(x),y)


def get_pg(x:ndarray,y:ndarray,tree_count:int)->ndarray:
    '''
    ### Abstract
        Mining pg using random forest model
    ### Parameters
        - x：The value of each spatial variable for each plot
        - y：Label for each plot (later land use type)
        - tree_count：Number of decision trees in a random forest

    ### Return
        The pg shape of each block is n rows and m columns, n is the number of plots and m is the number of land types
    '''
    type_count=len(list(set(y)))
    sample_count=x.shape[0]
    pg=np.zeros(shape=(sample_count,type_count))
    predicted_samples=np.zeros(shape=(sample_count,tree_count))

    forest=RandomForestClassifier(n_estimators=tree_count,random_state=2,oob_score=True,bootstrap=True)
    forest.fit(x,y)
    print('OOB Score:',forest.oob_score_)

    # 记录每一棵树对x的预测值
    for tree_index,tree in enumerate(forest.estimators_):
        predicted_samples[:,tree_index]=tree.predict(x)

    for sample_index,predicted_sample in enumerate(predicted_samples):
        for predicted_value in y:
            pg[sample_index,int(predicted_value)]=np.sum(predicted_sample==predicted_value)
    pg=pg/tree_count

    return pg

def write_to_shapefile(output_shapefile_name:str,pg:ndarray,mapping:dict,FID:ndarray,error_value:float)->None:
    '''
    ### Abstract
        Write pg to shapefile
    ### Parameters
        - output_shapefile_name：The name of the output shapefile
        - pg：pg for each land use type in each region
        - mapping：Mapping dictionary of land use type names
        - FID：FID after removing blocks with error values in the spatial variable field
        - error_value：Error value during partition statistics

    ### Return
        none
    '''
    file: DataSource = ogr.Open(output_shapefile_name, 1)
    layer: Layer = file.GetLayer()

    keys=mapping.keys()
    for key in keys:
        field_defn = FieldDefn('pg_'+key, ogr.OFTReal)
        layer.CreateField(field_defn)

    feature:Feature
    for feature in layer:
        for key in keys:
            feature.SetField('pg_'+key,error_value)
        layer.SetFeature(feature)

    for index,fid in enumerate(FID):
        feature=layer.GetFeature(fid)
        for key in keys:
            feature.SetField('pg_'+key,pg[index,mapping[key]])
        layer.SetFeature(feature)
    

def write_to_csv(output_csvfile_name:str,pg:ndarray,mapping:dict,FID:ndarray)->None:
    '''
    ### Abstract
        Write pg to the csv file
    ### Parameters
        - output_csvfile_name：The output csv file name
        - pg：pg for each land use type in each region
        - mapping：Mapping dictionary of land use type names
        - FID：FID after removing blocks with error values in the spatial variable field

    ### Return
        none
    '''
    keys=mapping.keys()
    header='FID,'
    for key in keys:
        header+='pg_'+key+','
    header=header[:-1]+'\n'

    body = ''
    for index,fid in enumerate(FID):
        body += str(fid)+','
        for key in keys:
            body += str(pg[index, mapping[key]])+','
        body = body[:-1]+'\n'

    file = open(output_csvfile_name, 'w')
    file.write(header+body)
    file.close()

def mining_pg_RF(input_file_name:str,output_shapefile_name:str,output_csvfile_name:str,label_field_name:str,spatial_variable_field_name_list:list,tree_count:int,error_value:float=-99999):
    '''
    ### Abstract
        To utilize the Random Forest algorithm to calculate the overall development probability by using parcels as samples, the zonal statistical values of parcels on various spatial variables as features, and the later land use types as labels.
    ### Parameters
        - input_file_name：the address of the zonal statistics shapefile.
        - output_shapefile_name：the output address of the shapefile result file.
        - output_csvfile_name：the output address of the CSV result file.
        - label_field_name：the field name of the later land use types.
        - spatial_variable_field_name_list：a list of field names for various spatial variables.
        - tree_count： the number of decision trees in the Random Forest.

    ### Return
        none
    '''
    copy_shapefile(input_file_name,output_shapefile_name)
    
    FID,x,y=make_dataset(input_file_name,label_field_name,spatial_variable_field_name_list,error_value)
    encoded_y,mapping=encode_y(y)

    pg=get_pg(x,encoded_y,tree_count)
    
    write_to_shapefile(output_shapefile_name,pg,mapping,FID,error_value)
    write_to_csv(output_csvfile_name,pg,mapping,FID)

    return


if __name__=='__main__':
    mining_pg_RF(
        input_file_name=r"E:\UrbanVCA_Python\output\zonal.shp",
        output_shapefile_name=r"E:\UrbanVCA_Python\output\pg.shp",
        output_csvfile_name=r"E:\UrbanVCA_Python\output\pg.csv",
        label_field_name='after',
        spatial_variable_field_name_list=['dem','highway','metro','osm','resident','restaurant'],
        tree_count=90)


