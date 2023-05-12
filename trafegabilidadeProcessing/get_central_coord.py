from qgis.core import QgsRasterLayer, QgsPointXY

def get_raster_center_point(raster_path):
    # Carregar o raster
    raster_layer = QgsRasterLayer(raster_path, 'raster')

    # Obter as dimensões do raster
    cols = raster_layer.width()
    rows = raster_layer.height()

    # Obter a extensão do raster em coordenadas geográficas
    extent = raster_layer.extent()
    xmin, ymin, xmax, ymax = extent.toRectF().getCoords()

    # Calcular as coordenadas centrais do raster
    x_center = xmin + (xmax - xmin) / 2
    y_center = ymin + (ymax - ymin) / 2

    # Criar um objeto QgsPointXY para representar as coordenadas centrais do raster
    center_point = QgsPointXY(x_center, y_center)

    # # Obter a projeção espacial do raster
    # projection = raster_layer.crs()

    # # Definir a projeção espacial do objeto QgsPointXY para a projeção espacial do raster
    # center_point.setCrs(projection)

    return center_point
