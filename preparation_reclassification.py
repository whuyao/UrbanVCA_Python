from osgeo import ogr
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import FieldDefn

from utils import copy_shapefile
import os
os.environ['PROJ_LIB'] = r'C:\Users\dell\AppData\Local\Programs\Python\Python38\Lib\site-packages\osgeo\data\proj'

def get_field_names(file_name:str) -> list:
    '''
    ### Abstract
        Get the names of all the fields of the shapefile file
    ### Parameters
        - The filename of the shapefile
        
    ### Return
        A list of all field names
    '''
    file: DataSource = ogr.Open(file_name)
    layer:Layer = file.GetLayer()

    field_count=layer.GetLayerDefn().GetFieldCount()

    field_names=[]
    for i in range(field_count):
        field_defn:FieldDefn=layer.GetLayerDefn().GetFieldDefn(i)
        field_names.append(field_defn.GetName())

    return field_names

def get_types(file_name:str, field_name:str) -> list:
    '''
    ### Abstract
        Get all the values of a field, then remove the same values
    ### Parameters
        - file_name: The filename of the shapefile
        - field_name: Name of a field in shapefile

    ### Return
        A list of specified fields with the same values removed
    '''
    file: DataSource = ogr.Open(file_name)
    layer:Layer = file.GetLayer()

    values=[]
    for feature in layer:
        feature:Feature=feature
        value=feature.GetField(field_name)
        values.append(value)

    # 去除相同值
    return list(set(values))

def reclassification(input_file_name:str, output_file_name:str, reclass_field_name:str, new_field_name:str, reclass_dict:dict) -> None:
    '''
    ### Abstract
        Based on the reclassification dictionary, the value of the reclassification field is converted to a new value and then the new field is written
    ### Parameters
        - input_file_name: the file path of the land use type file
        - out_file_name: output path of the result file
        - reclass_field_name: the field name representing land use types
        - new_field_name: the field name for the new land use types after reclassification

    ### Return
        none
    '''

    copy_shapefile(input_file_name,output_file_name)
    output_file:DataSource = ogr.Open(output_file_name,1)
    output_layer:Layer = output_file.GetLayer()


    new_field_defn:FieldDefn = ogr.FieldDefn(new_field_name, ogr.OFTString)
    output_layer.CreateField(new_field_defn)


    feature:Feature
    for feature in output_layer:

        reclass_value=feature.GetField(reclass_field_name)
        new_value=reclass_dict[reclass_value]
        feature.SetField(new_field_name, new_value)
        output_layer.SetFeature(feature)

    return

if __name__=='__main__':
    # print(get_types('UrbanVCA_Python/UrbanVCA_APP_v2.2/data/2018.shp', 'DLMC'))
    # print(get_field_names('UrbanVCA_Python/UrbanVCA_APP_v2.2/data/2018.shp'))

    reclassification(
        input_file_name=r"E:\UrbanVCA_Python\data\2015.shp",
        output_file_name=r"E:\UrbanVCA_Python\output\2015_re.shp",
        reclass_field_name='DLMC',
        new_field_name='new',
        reclass_dict={'city':0, 'water':1, 'farmland':2, 'garden':3, 'woodland':4})

    reclassification(
        input_file_name=r"E:\UrbanVCA_Python\data\2018.shp",
        output_file_name=r"E:\UrbanVCA_Python\output\2018_re.shp",
        reclass_field_name='DLMC',
        new_field_name='new',
        reclass_dict={'city':0, 'water':1, 'farmland':2, 'garden':3, 'woodland':4})
