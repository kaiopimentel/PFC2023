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
    slope_data = np.arctan(np.sqrt((np.gradient(elevation_data, axis=0) / xres) * 2 + (np.gradient(elevation_data, axis=1) / yres) * 2)) * 180 / np.pi

    # Criar o VRT temporário
    vrt = '<VRTDataset rasterXSize="%d" rasterYSize="%d">' % (src.RasterXSize, src.RasterYSize)
    vrt += '<VRTRasterBand dataType="Float32" band="1">'
    vrt += '<NoDataValue>-9999</NoDataValue>'
    vrt += '<ComplexSource>'
    vrt += '<SourceFilename relativeToVRT="1">%s</SourceFilename>' % os.path.basename(ds)
    vrt += '<SourceBand>1</SourceBand>'
    vrt += '<SourceProperties RasterXSize="%d" RasterYSize="%d" DataType="Float32" BlockXSize="%d" BlockYSize="%d"/>' % (src.RasterXSize, src.RasterYSize, band.GetBlockSize()[0], band.GetBlockSize()[1])
    vrt += '<SrcRect xOff="0" yOff="0" xSize="%d" ySize="%d"/>' % (src.RasterXSize, src.RasterYSize)
    vrt += '<DstRect xOff="0" yOff="0" xSize="%d" ySize="%d"/>' % (src.RasterXSize, src.RasterYSize)
    vrt += '<NODATA>-9999</NODATA>'
    vrt += '</ComplexSource>'
    vrt += '</VRTRasterBand>'
    vrt += '</VRTDataset>'

    # Abrir o VRT temporário
    mem_drv = gdal.GetDriverByName('MEM')
    vrt_ds = mem_drv.Create('', src.RasterXSize, src.RasterYSize, 1, gdal.GDT_Float32)
    vrt_ds.SetMetadata({'nodata': '-9999'})
    vrt_ds.SetMetadata({'source_0': ds})
    vrt_ds.SetMetadata({'source_0_band': '1'})
    vrt_ds.SetMetadata({'source_0_noData': '-9999'})
    vrt_ds.SetMetadata({'source_0_resampling': 'nearest'})
    vrt_ds.SetMetadata({'source_0_transformation': '1 0 0 0 1 0'})

    vrt_ds.SetMetadataItem('xml:VRT', vrt)

    out_band = vrt_ds.GetRasterBand(1)
    out_band.WriteArray(slope_data)
    out_band.FlushCache()

    return QgsRasterLayer(vrt_ds.GetDescription(), 'slope')