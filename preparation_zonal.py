from osgeo import ogr, gdal
from osgeo.ogr import DataSource
from osgeo.ogr import Layer
from osgeo.ogr import Feature
from osgeo.ogr import FieldDefn

from osgeo.gdal import Dataset
from osgeo.gdal import Band
import numpy as np
from numpy import ndarray
import matplotlib.pyplot as plt

from utils import copy_shapefile
from utils import get_feature_list
from utils import apart_multipolygon
from utils import delete_all_feature
from utils import add_all_feature

from enum import Enum
import os
os.environ['PROJ_LIB'] = r'C:\Users\dell\AppData\Local\Programs\Python\Python38\Lib\site-packages\osgeo\data\proj'

class StatisticMethod(Enum):
    mean = np.mean
    max = np.max
    min = np.min


class RasterFileConfig():
    def __init__(self, file_name: str, field_name: str, statistic_method):
        self.file_name = file_name # File name of the tiff image
        self.field_name = field_name # The statistics of this raster are written to the field name of the shapefile file
        self.statistic_method = statistic_method # Statistical methods (mean, maximum, minimum)


def get_raster_parameter(raster_file: Dataset) -> tuple:
    '''
    ### Abstract
        To get the parameters of the tiff image
    ### Parameters
        - raster_file：Dataset of tiff images

    ### Return
        Transform of tiff image, first band, nodata value
    '''
    geotransform = raster_file.GetGeoTransform()
    raster_band: Band = raster_file.GetRasterBand(1)
    raster_nodata = raster_band.GetNoDataValue()

    return (geotransform, raster_band, raster_nodata)


def get_new_geotransform(envelope: tuple, geotransform: tuple) -> tuple:
    '''
    ### Abstract
        Calculate the transformation parameters of the rasterized block
    ### Parameters
        - envelope：Parcel outsourced rectangle
        - geotansform：Transform parameters for tiff images
        
    ### Return
        Transform parameters for tiff images
    '''
    polygon_x_min = envelope[0]
    polygon_y_max = envelope[3]

    pixel_width = geotransform[1]
    pixel_height = geotransform[5]

    return (polygon_x_min, pixel_width, 0, polygon_y_max, 0, pixel_height)


def get_offset_and_count(envelope: tuple, geotransform: tuple) -> tuple:
    '''
    ### Abstract
        Calculate the distance of the outlying rectangle of the plot from the left and top of the tiff image, as well as the number of rows and columns of the rectangle
    ### Parameters
        - envelope：Parcel outsourced rectangle
        - geotansform：Transform parameters for tiff images

    ### Return
        - The number of squares on the left side of the block outlying rectangle from the left side of the tiff image
        - The number of cells above the tiff image from the top of the block outlying rectangle
        - The number of columns of rectangles around the block
        - The number of rows of rectangles around the block
    '''
    polygon_x_min, polygon_x_max, polygon_y_min, polygon_y_max = envelope

    raster_x = geotransform[0]
    raster_y = geotransform[3]
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]

    x_offset = abs(int((polygon_x_min-raster_x)/pixel_width))
    y_offset = abs(int((raster_y-polygon_y_max)/pixel_height))
    x_count = abs(int((polygon_x_max-polygon_x_min)/pixel_width))+1
    y_count = abs(int((polygon_y_max-polygon_y_min)/pixel_height))+1

    return (x_offset, y_offset, x_count, y_count)


def write_to_csv(raster_file_config_list: list, statistic_array: ndarray, output_csvfile_name: str) -> None:
    '''
    ### Abstract
        Write the statistics to a csv file
    ### Parameters
        - raster_file_config_list：A list of multiple tiff image configurations
        - statistic_array：Statistical result array, n rows m columns, n represents the number of plots, m represents the number of tiff images
        - output_csvfile_name：The name of the output csv file

    ### Return
        none
    '''
    header = 'FID,'
    raster_file_config: RasterFileConfig
    for raster_file_config in raster_file_config_list:
        header += raster_file_config.field_name+','
    header = header[:-1]+'\n'

    body = ''
    rows, cols = statistic_array.shape
    for row_index in range(rows):
        body += str(row_index)+','
        for col_index in range(cols):
            body += str(statistic_array[row_index, col_index])+','
        body = body[:-1]+'\n'

    file = open(output_csvfile_name, 'w')
    file.write(header+body)
    file.close()


def write_to_shapefile(raster_file_config_list: list, statistic_array: ndarray, feature_list: list, output_shapefile_name: str) -> None:
    '''
    ### Abstract
        Write the statistics result to shapefile
    ### Parameters
        - raster_file_config_list：A list of multiple tiff image configurations
        - statistic_array：Statistical result array, n rows m columns, n represents the number of plots, m represents the number of tiff images
        - feature_list：Plot list
        - output_shapefile_name：The name of the output shapefile

    ### Return
        none
    '''
    file: DataSource = ogr.Open(output_shapefile_name, 1)
    layer: Layer = file.GetLayer()

    delete_all_feature(layer)
    add_all_feature(layer, feature_list)

    raster_file_config: RasterFileConfig
    for raster_file_config in raster_file_config_list:
        field_defn = FieldDefn(raster_file_config.field_name, ogr.OFTReal)
        layer.CreateField(field_defn)

    feature: Feature
    for feature_index, feature in enumerate(layer):
        for raster_index, raster_file_config in enumerate(raster_file_config_list):
            value = statistic_array[feature_index, raster_index]
            feature.SetField(raster_file_config.field_name, value)
        layer.SetFeature(feature)


def zonal(polygon_file_name: str, raster_file_config_list: list, output_csvfile_name: str, output_shapefile_name: str, error_value: float = -99999):
    '''
    ### Abstract
        zonal statistics. calculating statistical values (mean, maximum, minimum) of the pixels covered by the parcels.
    ### Parameters
        - polygon_file_name：the address of the matched land use type shapefile
        - raster_file_config_list：list of configurations for multiple TIFF images
        - output_csvfile_name：the address of the CSV result file
        - output_shapefile_name：output address of the shapefile result file

    ### Return
        none
    '''
    polygon_file: DataSource = ogr.Open(polygon_file_name)
    polygon_layer: Layer = polygon_file.GetLayer()

    ogr_driver: ogr.Driver = ogr.GetDriverByName('Memory')
    gdal_driver: gdal.Driver = gdal.GetDriverByName('MEM')

    polygon_feature_list = get_feature_list(polygon_file_name)
    polygon_feature_list = apart_multipolygon(polygon_feature_list)

    statistic_array = np.zeros(shape=(len(polygon_feature_list), len(raster_file_config_list)))

    raster_file_config: RasterFileConfig
    polygon_feature: Feature

    for raster_index, raster_file_config in enumerate(raster_file_config_list):
        raster_file: Dataset = gdal.Open(raster_file_config.file_name)

        geotransform, raster_band, raster_nodata = get_raster_parameter(raster_file)
        raster_band: Band


        for feature_index, polygon_feature in enumerate(polygon_feature_list):
            envelope = polygon_feature.GetGeometryRef().GetEnvelope()

            new_geotransform = get_new_geotransform(envelope, geotransform)
            x_offset, y_offset, x_count, y_count = get_offset_and_count(envelope, geotransform)

            temp_polygon_file: DataSource = ogr_driver.CreateDataSource('temp')
            temp_polygon_layer: Layer = temp_polygon_file.CreateLayer('polygon', polygon_layer.GetSpatialRef(), ogr.wkbPolygon)
            temp_polygon_layer.CreateFeature(polygon_feature.Clone())

            temp_raster_file: Dataset = gdal_driver.Create('', x_count, y_count, 1, gdal.GDT_Byte)
            temp_raster_file.SetGeoTransform(new_geotransform)


            gdal.RasterizeLayer(temp_raster_file, [1], temp_polygon_layer, burn_values=[1])
            polygon_mask = temp_raster_file.GetRasterBand(1).ReadAsArray()


            raster_data = raster_band.ReadAsArray(x_offset, y_offset, x_count, y_count)
            

            masked_array = np.ma.MaskedArray(raster_data, mask=np.logical_or(raster_data == raster_nodata, np.logical_not(polygon_mask)))
            statistic_value = raster_file_config.statistic_method(masked_array)

            if str(statistic_value) == '--':
                masked_array = np.ma.MaskedArray(raster_data, mask=raster_data == raster_nodata)
                statistic_value = raster_file_config.statistic_method(masked_array)
                if str(statistic_value) == '--':
                    statistic_value = 0

            statistic_array[feature_index, raster_index] = statistic_value

    copy_shapefile(polygon_file_name, output_shapefile_name)
    write_to_csv(raster_file_config_list, statistic_array, output_csvfile_name)
    write_to_shapefile(raster_file_config_list, statistic_array,polygon_feature_list, output_shapefile_name)


if __name__ == '__main__':
    zonal(
        polygon_file_name=r"E:\UrbanVCA_Python\output\match.shp",
        raster_file_config_list=[
            RasterFileConfig(
                r"E:\UrbanVCA_Python\data\dem.tif", 'dem', StatisticMethod.mean),
            RasterFileConfig(
                r"E:\UrbanVCA_Python\data\highway.tif", 'highway', StatisticMethod.mean),
            RasterFileConfig(
                r"E:\UrbanVCA_Python\data\metro.tif", 'metro', StatisticMethod.mean),
            RasterFileConfig(
                r"E:\UrbanVCA_Python\data\osm.tif", 'osm', StatisticMethod.mean),
            RasterFileConfig(
                r"E:\UrbanVCA_Python\data\resident.tif", 'resident', StatisticMethod.mean),
            RasterFileConfig(
                r"E:\UrbanVCA_Python\data\restaurant.tif", 'restaurant', StatisticMethod.mean),
        ],
        output_csvfile_name=r"E:\UrbanVCA_Python\output\zonal.csv",
        output_shapefile_name=r"E:\UrbanVCA_Python\output\zonal.shp"
        )

