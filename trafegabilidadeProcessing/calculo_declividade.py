import os
import numpy as np
from osgeo import gdal, osr
from qgis.core import QgsRasterLayer, QgsProject
import tempfile

def reproject_raster_to_utm(src_ds):
    # Obter a transformação de coordenadas do sistema de origem para UTM
    src_srs = osr.SpatialReference()
    src_srs.ImportFromWkt(src_ds.GetProjection())
    utm_srs = src_srs.CloneGeogCS()
    longitude_origin = src_srs.GetProjParm(osr.SRS_PP_CENTRAL_MERIDIAN)
    utm_zone = int((longitude_origin + 180) / 6) + 1
    utm_srs.SetUTM(utm_zone, src_srs.GetAttrValue('AUTHORITY', 1) == 'N')

    # Reprojetar o raster para UTM
    utm_ds = gdal.Warp('', src_ds, format='VRT', dstSRS=utm_srs)
    return utm_ds



def calculate_slope(raster_layer, output_path):
    ds = raster_layer.source()
    # Abrir o arquivo raster
    src = gdal.Open(ds)
    
    # Reprojetar o raster para UTM
    utm_src = reproject_raster_to_utm(src)

    band = utm_src.GetRasterBand(1)
    gt = utm_src.GetGeoTransform()
    
    elevation_data = band.ReadAsArray()
    xres = gt[1]
    yres = gt[5]
    slope_data = np.arctan(np.sqrt((np.gradient(elevation_data, axis=0) / xres) ** 2 + (np.gradient(elevation_data, axis=1) / yres) ** 2)) * 180 / np.pi

    # Criar uma máscara para os pixels sem dados
    no_data_mask = elevation_data == band.GetNoDataValue()
    masked_slope_data = np.ma.masked_where(no_data_mask, slope_data)

    # Criar o arquivo de saída
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_path, utm_src.RasterXSize, utm_src.RasterYSize, 1, gdal.GDT_Float32)

    if out_ds is None:
        print("Não foi possível criar o arquivo de saída. Verifique o caminho e as permissões do arquivo.")
        return

    out_ds.SetGeoTransform(gt)
    out_ds.SetProjection(utm_src.GetProjection())
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(masked_slope_data.filled(np.nan))
    out_band.FlushCache()
    out_band.SetNoDataValue(np.nan)
    out_ds = None

# # Substitua a string abaixo com o nome da camada
# input_layer_name = 'SRTMGL3[Memory]'
# input_layer = QgsProject.instance().mapLayersByName(input_layer_name)[0]

# # Criar um arquivo temporário no disco
# temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')
# temp_file.close()

# # Calcular a declividade e criar a camada temporária em arquivo
# calculate_slope(input_layer, temp_file.name)

# # Carregar a camada de declividade no QGIS
# slope_layer = QgsRasterLayer(temp_file.name, 'Slope')
# QgsProject.instance().addMapLayer(slope_layer)

# # Remover o arquivo temporário do disco quando não for mais necessário
# # (exemplo: ao fechar o QGIS ou ao executar algum outro código)
# os.remove(temp_file.name)