import os
import numpy as np
from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsProject

def calculate_slope(raster_layer):
    ds = raster_layer.source()
    # Abrir o arquivo raster
    src = gdal.Open(ds)
    band = src.GetRasterBand(1)
    gt = src.GetGeoTransform()
    
    # Ler a matriz do raster e calcular a declividade
    elevation_data = band.ReadAsArray()
    xres = gt[1]
    yres = gt[5]
    slope_data = np.arctan(np.sqrt((np.gradient(elevation_data, axis=0) / xres) ** 2 + (np.gradient(elevation_data, axis=1) / yres) ** 2)) * 180 / np.pi
    
    # Criar o arquivo de saída
    driver = gdal.GetDriverByName('MEM')
    out_ds = driver.Create('', src.RasterXSize, src.RasterYSize, 1, gdal.GDT_Float32)
    
    if out_ds is None:
        print("Não foi possível criar o arquivo de saída. Verifique o caminho e as permissões do arquivo.")
        return

    out_ds.SetGeoTransform(gt)
    out_ds.SetProjection(src.GetProjection())
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(slope_data)
    out_band.FlushCache()
    out_band.SetNoDataValue(-9999)

    # Fechar o dataset para salvar as alterações
    # out_ds.FlushCache()

    # Criar a camada raster temporária
    out_layer = QgsRasterLayer('data provider=mem:;type=gdal;'+out_ds.GetMetadataItem('TIFFTAG_IMAGEDESCRIPTION'), 'output')

    # Adicionar a camada raster temporária ao mapa do QGIS
    QgsProject.instance().addMapLayer(out_layer)

    return out_layer

# # Substitua as seguintes strings com o nome da camada e o caminho de saída
# input_layer_name = 'MDE_26124so_v1'

# input_layer = QgsProject.instance().mapLayersByName(input_layer_name)[0]
# output_ds = calculate_slope(input_layer)

# # Criar uma camada do QGIS a partir do dataset em memória e adicioná-la ao projeto
# output_uri = '/vsimem/slope.tif'
# gdal.GetDriverByName('GTiff').CreateCopy(output_uri, output_ds)
# slope_layer = QgsRasterLayer(output_uri, 'Slope', 'gdal')
# QgsProject.instance().addMapLayer(slope_layer)

