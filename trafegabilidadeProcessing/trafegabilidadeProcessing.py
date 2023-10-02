# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import sys
sys.dont_write_bytecode = True
import os
import shutil
from osgeo import gdal
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.utils import iface
from qgis.gui import QgsMapCanvas
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import (QgsRectangle,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingUtils,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsPointXY,
                       QgsFeature,
                       QgsGeometry,
                       QgsProject,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsMapLayer,
                       QgsColorRampShader,
                       QgsRasterShader,
                       QgsSingleBandPseudoColorRenderer, 
                       QgsColorRampShader, 
                       QgsRasterShader,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorDestination,
                       QgsApplication,
                       QgsLayerTreeLayer
                       )
from qgis.PyQt.QtGui import QColor
from qgis import processing

from numpy import array
import requests
from pyproj import CRS

from .cartography import reprojectPoints, mi2inom, inom2mi
from .calculo_declividade import calculate_slope
from .get_central_coord import get_raster_center_point
from .get_utm_zone import get_zone_number

from .classList import class_list, rest_classes, imp_classes

class TrafegabilidadeProcessingAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """
    
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    # INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    MI = 'MI'
    SITUATION = 'SITUATION'
    # FRAME = 'FRAME'
    CRS = 'CRS' 
    BOOLLOADLAYERS = 'BOOLLOADLAYERS'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return TrafegabilidadeProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Mapa de Trafegabilidade'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return None

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr('''
        Este plugin utiliza-se de parâmetros fornecidos pelo usuário para elaboração de mapas de trafegabilidade de maneira automatizada
        ''')
    
    def __init__(self):
        super().__init__()
        # Limpe o cache ao iniciar o algoritmo
        self.clear_pycache(os.path.dirname(__file__))

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterString(
                self.MI,
                self.tr('MI'),
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.SITUATION,
                self.tr('Situação de deslocamento'),
                ['Viatura sobre rodas', 'Viatura sobre lagartas', 'Deslocamento a pé'],
                defaultValue = 0
            )

        )

        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('SRC da Moldura'),
                'ProjectCrs'
			)
		)

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        # self.addParameter(
        #     QgsProcessingParameterFeatureSink(
        #         self.FRAME,
        #         self.tr('Moldura')
        #     )
        # )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.BOOLLOADLAYERS,
                self.tr('Carregar camadas intermediárias'),
                defaultValue=False
            )
        ) 

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output Raster')
            )
        )                     

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        from qgis.core import QgsProject

        nome = self.parameterAsString(
            parameters,
            self.MI,
            context
        )

        crs = self.parameterAsCrs(
            parameters,
            self.CRS,
            context
        )

        situation = self.parameterAsInt(
            parameters,
            self.SITUATION,
            context
        )

        boolloadlayers = self.parameterAsBool(
            parameters, 
            self.BOOLLOADLAYERS, 
            context
        )

        if situation == 0:
            #vtr sobre rodas
            restrictive_slope = 6
            impediment_slope=17
        elif situation == 1:
            #vtr sobre lagartas
            restrictive_slope = 17
            impediment_slope = 26
        elif situation == 2:
            #tropa a pé
            restrictive_slope = 26
            impediment_slope = 45
        ###############################################################################################################################
        
        url_with_params = "type=xyz&url=https%3A//mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0&crs=EPSG3857"
        google_layer = QgsRasterLayer(url_with_params, "Google Satellite", "wms")

        if not google_layer.isValid():
            print("Camada não foi carregada corretamente!")
        else:
            # Adiciona a camada de satélite
            QgsProject.instance().addMapLayer(google_layer, False)

            # Coloque a camada de satélite na parte inferior da pilha de camadas
            root = QgsProject.instance().layerTreeRoot()
            google_layer_node = QgsLayerTreeLayer(google_layer)
            cloned_node = google_layer_node.clone()
            root.insertChildNode(0, cloned_node)  # 0 significa a primeira posição
            root.removeChildNode(google_layer_node)
        
        
        # LFTools
        # Checking for geographic coordinate reference system
        if not crs.isGeographic():
            crsGeo = QgsCoordinateReferenceSystem(crs.geographicCrsAuthId())
            coordinateTransformer = QgsCoordinateTransform()
            coordinateTransformer.setDestinationCrs(crs)
            coordinateTransformer.setSourceCrs(crsGeo)

        # Output Definition
        Fields = QgsFields()
        Fields.append(QgsField('inom', QVariant.String))
        Fields.append(QgsField('mi', QVariant.String))
        Fields.append(QgsField(self.tr('escala'), QVariant.Int))
        GeomType = QgsWkbTypes.Polygon

        # self.FRAME = 'TEMPORARY_OUTPUT'
        # (sink, dest_id) = self.parameterAsSink(
        #     parameters,
        #     self.FRAME,
        #     context,
        #     Fields,
        #     GeomType,
        #     crs
        # )


        nome = nome.upper()
        lista = nome.split('-')

        # Converter MI para INOM
        dicionario = mi2inom

        tipo = 0
        if tipo == 0:

            if lista[0] not in dicionario:
                raise QgsProcessingException(self.tr('erro: MI não existe!'))

            if len(lista)>1:
                lista = dicionario[lista[0]].split('-') + lista[1:]
            else:
                lista = dicionario[lista[0]].split('-')

        if len(lista)<2:
            raise QgsProcessingException(self.tr('erro: nome incorreto!'))

        # Hemisphere
        if lista[0][0] == 'S':
            sinal = -1
        elif lista[0][0] == 'N':
            sinal = 1
        else:
            raise QgsProcessingException(self.tr('erro: hemisfério incorreto!'))

        # Latitude inicial
        if sinal == -1:
            lat = sinal*4*(ord(lista[0][1])-64)
        else:
            lat = sinal*4*(ord(lista[0][1])-64) - 4

        # Longitude inicial
        if int(lista[1])<1 or int(lista[1])>60:
            raise QgsProcessingException(self.tr('erro: fuso incorreto!'))
        lon = 6*int(lista[1]) - 186

        if len(lista) ==2:
            d_lon = 6.0
            d_lat = 4.0
            coord = [[QgsPointXY(lon, lat), QgsPointXY(lon, lat+d_lat), QgsPointXY(lon+d_lon, lat+d_lat), QgsPointXY(lon+d_lon, lat), QgsPointXY(lon, lat)]]
            escala = 1e6
        else:
            dic_delta  =  {'500k': {'Y':[0, 0], 'V':[0, 2.0], 'X':[3.0, 2.0], 'Z':[3.0, 0]},
                                '250k': {'C':[0, 0], 'A':[0, 1.0], 'B':[1.5, 1.0], 'D':[1.5, 0]},
                                '100k': {'IV':[0, 0], 'I':[0, 0.5], 'II':[0.5, 0.5], 'V':[0.5, 0], 'III':[1.0, 0.5], 'VI': [1.0, 0]},
                                '50k': {'3':[0, 0], '1':[0, 0.25], '2':[0.25, 0.25], '4':[0.25, 0]},
                                '25k': {'SO':[0, 0], 'NO':[0, 0.125], 'NE':[0.125, 0.125], 'SE':[0.125, 0]},
                                '10k': {'E':[0, 0], 'C':[0, 0.125/3], 'D':[0.125/2, 0.125/3], 'F':[0.125/2, 0], 'A':[0, 2*0.125/3], 'B':[0.125/2, 2*0.125/3] },
                                '5k': {'III':[0, 0], 'I':[0, 0.125/3/2], 'II':[0.125/2/2, 0.125/3/2], 'IV':[0.125/2/2, 0]},
                                '2k': {'4':[0, 0], '1':[0, 0.125/3/2/2], '2':[0.125/2/2/3, 0.125/3/2/2], '5':[0.125/2/2/3, 0], '3':[2*0.125/2/2/3, 0.125/3/2/2], '6':[2*0.125/2/2/3,0]},
                                '1k': {'C':[0, 0], 'A':[0, 0.125/3/2/2/2], 'B':[0.125/2/2/3/2, 0.125/3/2/2/2], 'D':[0.125/2/2/3/2, 0]}
                                }
            escalas = ['500k', '250k', '100k', '50k', '25k', '10k', '5k', '2k', '1k']
            for k, cod in enumerate(lista[2:]):
                d_lon = dic_delta[escalas[k]][cod][0]
                d_lat = dic_delta[escalas[k]][cod][1]
                lon += d_lon
                lat += d_lat
            # feedback.pushInfo(self.tr('Origem')+': Longitude = {} e Latitude = {}'.format(lon, lat))
            valores = array([[3.0, 1.5, 0.5, 0.25, 0.125, 0.125/2, 0.125/2/2, 0.125/2/2/3, 0.125/2/2/3/2],
                                   [2.0, 1.0, 0.5, 0.25, 0.125, 0.125/3, 0.125/3/2, 0.125/3/2/2, 0.125/3/2/2/2]])
            d_lon = valores[0,k]
            d_lat = valores[1,k]
            coord = [[QgsPointXY(lon         , lat),
                          QgsPointXY(lon          , lat+d_lat),
                          QgsPointXY(lon+d_lon, lat+d_lat),
                          QgsPointXY(lon+d_lon, lat),
                          QgsPointXY(lon          , lat)]]
            escala = int(escalas[k][:-1])*1000

            feat = QgsFeature()
        geom = QgsGeometry.fromPolygonXY(coord)
        # Coordinate Transformations (if needed)
        geom = geom if crs.isGeographic() else reprojectPoints(geom, coordinateTransformer)
        if tipo == 0:
            mi = nome
            lista = mi.split('-')
            inom = dicionario[lista[0]]
            if len(lista)>1:
                resto = ''
                for k in range(1,len(lista)):
                    resto += lista[k] +'-'
                inom += '-' + resto[:-1]
            att = [inom, mi, escala]
        else:
            inom = nome
            lista = inom.split('-')
            inom100k = ''
            if len(lista) >= 5:
                for t in range(5):
                    inom100k += lista[t] + '-'
                inom100k = inom100k[:-1]
                if inom100k in inom2mi:
                    mi = inom2mi[inom100k]
                    for k in range(5,len(lista)):
                        mi += '-' + lista[k]
                else:
                    mi = None
            else:
                mi = None

            att = [inom, mi, escala]
        feat.setGeometry(geom)
        feat.setAttributes(att)
        
        from qgis.core import QgsVectorLayer, QgsVectorLayerUtils


        layer_teste = QgsVectorLayer("Polygon?crs=EPSG:4326", f"Moldura_{nome}", "memory")
        QgsProject.instance().addMapLayer(layer_teste)
        sink2 = layer_teste.dataProvider()
        sink2.addFeature(feat, QgsFeatureSink.FastInsert)
        dest_id = layer_teste.id()

        ###############################################################################################################################
        #OpenTopography

        outputs = {}

        if crs.authid() != "EPSG:4326":
            extent = QgsCoordinateTransform(
                crs,
                QgsCoordinateReferenceSystem("EPSG:4326"),
                QgsProject.instance(),
            ).transformBoundingBox(extent)

        extent = geom.boundingBox()
        south = extent.yMinimum()
        north = extent.yMaximum()
        west = extent.xMinimum()
        east = extent.xMaximum()

        parameters['API_key'] = '2f976117b55394b5ba0915c318258d9a'
        parameters['Extent'] = extent
        parameters['DEMs'] = 0

        dem_code = 'SRTMGL3'

        from qgis.core import QgsVectorLayer
        import requests

        def generate_output_path(base_path, suffix):
            base_name = os.path.splitext(os.path.basename(base_path))[0]
            directory = os.path.dirname(base_path)
            return os.path.join(directory, f"{base_name}_{suffix}.tif")

        dem_url = f'https://portal.opentopography.org/API/globaldem?demtype={dem_code}&south={south}&north={north}&west={west}&east={east}&outputFormat=GTiff'
        dem_url=dem_url + "&API_Key=" + parameters['API_key']

        dem_file = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        feedback.pushInfo(f"Dem file path: {os.path.abspath(dem_file)}")

        try:
            alg_params = {'URL': dem_url, 'OUTPUT': dem_file}
            processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        except:
            response = requests.request("GET", dem_url, headers={}, data={})
            raise QgsProcessingException(response.text.split('<error>')[1][:-8])

        raster_layer = QgsRasterLayer(dem_file, f'MDE_{nome}')
        if not raster_layer.isValid():
            feedback.pushInfo(f'Erro ao carregar o raster: {raster_layer.lastError().message()}')
        else:
            if boolloadlayers:
                QgsProject.instance().addMapLayer(raster_layer)
                raster_layer.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))  # Define explicitamente o SRC

        ###############################################################################################################################

        ############################################################ Descobrir Fuso UTM
        ponto_central = get_raster_center_point(dem_file)
        point_x = ponto_central.x()
        point_y = ponto_central.y()
        utm_zone = get_zone_number(point_y, point_x)
        south_hemisphere = True if point_y <= 0 else False
        crs = CRS.from_dict({'proj': 'utm', 'zone': utm_zone[0:2], 'south': south_hemisphere})
        epsg = crs.to_authority()
        ############################################################ Reprojetar

        reproj_path = generate_output_path(dem_file, 'reproj')
        processing.run("gdal:warpreproject", {
            'INPUT': dem_file,
            'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'TARGET_CRS': QgsCoordinateReferenceSystem(f'EPSG:{epsg[1]}'),
            'RESAMPLING': 0,
            'NODATA': None,
            'TARGET_RESOLUTION': 30,
            'OPTIONS': '',
            'DATA_TYPE': 0,
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'MULTITHREADING': False,
            'EXTRA': '',
            'OUTPUT': reproj_path
        })

        reproj_raster = QgsRasterLayer(reproj_path, f'REPROJ_{nome}')
        if not reproj_raster.isValid():
            feedback.pushInfo(f'Erro ao carregar o raster REPROJ: {reproj_raster.lastError().message()}')
        else:
            if boolloadlayers:
                QgsProject.instance().addMapLayer(reproj_raster)
                reproj_raster.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{epsg[1]}'))  # Define explicitamente o SRC

        slope_path = generate_output_path(dem_file, 'slope')
        processing.run("native:slope", {
            'INPUT': reproj_path,
            'Z_FACTOR': 1,
            'OUTPUT': slope_path
        })

        slope_raster = QgsRasterLayer(slope_path, f'SLOPE_{nome}')
        if not slope_raster.isValid():
            feedback.pushInfo(f'Erro ao carregar o raster SLOPE: {slope_raster.lastError().message()}')
        else:
            if boolloadlayers:    
                QgsProject.instance().addMapLayer(slope_raster)
        
        ############################################################ Mapa Temático
        formula = f'(0 + (A >= {restrictive_slope}) * 1 + (A >= {impediment_slope}) * 1)'
        thematic_raster_path = generate_output_path(dem_file, 'thematic')
        processing.run("gdal:rastercalculator", {
            'INPUT_A': slope_path,
            'BAND_A': 1,
            'FORMULA': formula,
            'NO_DATA': None,
            'RTYPE': 5,
            'OPTIONS': '',
            'EXTRA': '',
            'OUTPUT': thematic_raster_path
        })         

        # Defina o estilo de cores contínuas
        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
        color_ramp.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(0, QColor(0, 255, 0)),
            QgsColorRampShader.ColorRampItem(1, QColor(255, 255, 0)),
            QgsColorRampShader.ColorRampItem(2, QColor(255, 0, 0))

        ])
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(color_ramp)

        thematic_raster = QgsRasterLayer(thematic_raster_path, f'MapaTematico_{nome}')
        renderer = QgsSingleBandPseudoColorRenderer(thematic_raster.dataProvider(), 1, shader)
        thematic_raster.setRenderer(renderer)
        if not thematic_raster.isValid():
            feedback.pushInfo(f'Erro ao carregar o raster Mapa Temático: {thematic_raster.lastError().message()}')
        else:
            if boolloadlayers:    
                QgsProject.instance().addMapLayer(thematic_raster)
        
        # from qgis.core import QgsVectorLayer

        vectorized_layer_path = generate_output_path(dem_file, 'vectorized')[:-4] + '.gpkg'
        processing.run("gdal:polygonize", {
            'INPUT': thematic_raster_path,
            'BAND': 1,
            'FIELD': 'DN',
            'EIGHT_CONNECTEDNESS': True,
            'EXTRA': '',
            'OUTPUT': vectorized_layer_path
        })        
        vectorized_layer = QgsVectorLayer(vectorized_layer_path, 'vectorized_impeditivo')
        vectorized_layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{epsg[1]}'))
        
        duplicate_vectorized_layer = QgsVectorLayer(vectorized_layer.source(), "vectorized_restritivo", vectorized_layer.providerType())
        duplicate_vectorized_layer.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{epsg[1]}'))
        
        filter_expression = '"DN" = 2'
        vectorized_layer.setSubsetString(filter_expression)
        filter_expression_2 = '"DN" = 1'
        duplicate_vectorized_layer.setSubsetString(filter_expression_2)

        if boolloadlayers:
            QgsProject.instance().addMapLayer(vectorized_layer)
            QgsProject.instance().addMapLayer(duplicate_vectorized_layer)
        
        project = QgsProject.instance()
        project.setCrs(QgsCoordinateReferenceSystem(f'EPSG:{epsg[1]}'))

        # project.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

        import requests
        import tempfile
        from qgis.PyQt.QtCore import QUrl
        from qgis.core import QgsProject, QgsProcessingUtils, QgsMessageLog, Qgis
        from qgis.analysis import QgsNativeAlgorithms
        from qgis.core import QgsProcessingFeatureSourceDefinition

        # Register the native algorithms for processing.
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

        # Get the extent of the frame layer
        frame_layer = QgsProcessingUtils.mapLayerFromString(dest_id, context)

        # Check if the frame_layer is valid
        if frame_layer is None:
            QgsMessageLog.logMessage(f"No layer found with ID {dest_id}!", 'Mapa de Trafegabilidade', level=Qgis.Critical)
            raise ValueError(f"No layer found with ID {dest_id}!")

        # Check if the layer has a valid extent
        extent = frame_layer.extent()
        if extent is None or extent.isEmpty():
            QgsMessageLog.logMessage(f"The layer with ID {dest_id} has no valid extent!", 'Mapa de Trafegabilidade', level=Qgis.Critical)
            raise ValueError(f"The layer with ID {dest_id} has no valid extent!")

        # Get the coordinates for the extent
        south = extent.yMinimum()
        north = extent.yMaximum()
        west = extent.xMinimum()
        east = extent.xMaximum()

        # Define the bbox string
        bbox = f"{west},{south},{east},{north}"

        noinfo_classes = []
        empty = True
        imp_classes_sources = []
        rest_classes_sources = []
        edif_classes_sources = []
        classes_to_remove = []
        canvas = iface.mapCanvas()
        # canvas.freeze(True)
        for category in class_list:
            for classe in category['classes']:
                # Build WFS request URL
                params = {
                    "service": "WFS",
                    "request": "GetFeature",
                    "typeName": "ms:"+classe,
                    "srsName": f"EPSG:{epsg[1]}",
                    "bbox": bbox,
                    "outputFormat": "GML2",
                    "version": "1.0.0",
                }
                wfs_url = "https://bdgex.eb.mil.br/ms25"
                response = requests.get(wfs_url, params=params)

                # Check if the request was successful
                if response.status_code != 200:
                    QgsMessageLog.logMessage(f"Request failed with status code: {response.status_code}", 'Mapa de Trafegabilidade', level=Qgis.Critical)
                    raise ValueError(f"Request failed with status code: {response.status_code}")

                # Create a temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
                QgsMessageLog.logMessage("Temporary file created at:" + temp_file.name, 'Mapa de Trafegabilidade', level=Qgis.Info)

                # Write the response to a temporary GML file
                with open(temp_file.name, "w") as f:
                    f.write(response.text)
                temp_file.close()

                # Load the temporary GML file as a vector layer
                vector_layer = QgsVectorLayer(temp_file.name, classe, "ogr")

                # Set the coordinate reference system to EPSG:4326
                crs = QgsCoordinateReferenceSystem("EPSG:4326")
                vector_layer.setCrs(crs)

                # Check if the vector layer is valid
                # feedback.pushInfo(f'{classe}')
                if not vector_layer.isValid():
                    QgsMessageLog.logMessage(vector_layer.error().message(), 'Mapa de Trafegabilidade', level=Qgis.Critical)
                    raise ValueError("Vector layer failed to load!")

                # Perform clipping operation
                params = {
                    'INPUT': vector_layer,
                    'OVERLAY': frame_layer,
                    'OUTPUT': 'memory:'  # store output in memory
                }
                clip_result = processing.run("native:clip", params)

                # Get the clipped layer
                clipped_layer = clip_result['OUTPUT']
                
                # Add the clipped layer to the project
                aux = 'aux'
                string_to_find = "<gml:null>missing</gml:null>"
                
                
                if string_to_find in response.text:
                    noinfo_classes.append(category['type']+'_'+classe)
                elif clipped_layer.featureCount() > 0:
                    empty = False
                    QgsProject.instance().addMapLayer(clipped_layer)
                    if category['type'] == 'edif':
                        classe_rename = classe.replace("EDF_", "").replace("Edif_", "")
                        clipped_layer.setName(category['type']+'_'+classe_rename+'_output')
                        edif_classes_sources.append(clipped_layer)
                    else:
                        clipped_layer.setName(category['type']+'_'+classe+'_output')
                    # if boolloadlayers:
                    #     QgsProject.instance().addMapLayer(clipped_layer)
                    #     clipped_layer.setName(category['type']+'_'+classe+'_output')
                    # else:
                    #     aux = 'aux_aux'
                    if category['type'] == 'hid' or classe in imp_classes:
                        imp_classes_sources.append(clipped_layer.source())
                    elif classe in rest_classes:
                        rest_classes_sources.append(clipped_layer.source())
                    # if boolloadlayers == False:
                    #     QgsProject.instance().removeMapLayer(clipped_layer)
                    classes_to_remove.append(clipped_layer)
                else:
                    noinfo_classes.append(category['type']+'_'+classe)

                if not f'{type(clipped_layer.renderer())}' == "<class 'NoneType'>":
                    symbol = clipped_layer.renderer().symbol()
                    if clipped_layer.type() == QgsMapLayer.VectorLayer and clipped_layer.geometryType() == QgsWkbTypes.LineGeometry:
                        symbol.setWidth(0.8)
                        clipped_layer.triggerRepaint()                            
                    if category['type'] == 'veg':
                        symbol.setColor(QColor.fromRgb(50,200,50))
                    elif category['type'] == 'hid':
                        symbol.setColor(QColor.fromRgb(50,50,200))
                    elif category['type'] == 'out':
                        symbol.setColor(QColor.fromRgb(30,30,30)) 
                    elif category['type'] == 'edif':
                        symbol.setColor(QColor.fromRgb(0,0,0)) 
                      
      
        if empty == True:
            feedback.pushInfo('Sem vetores para esse MI')
        else:
            for classe in noinfo_classes:
                feedback.pushInfo(f"{category['type']+'_'+classe} não encontrado para este MI")
        
        merge_result = processing.run("native:mergevectorlayers", {'LAYERS':edif_classes_sources,'CRS':None,'OUTPUT':'TEMPORARY_OUTPUT'})
        edif_merge_layer = merge_result['OUTPUT']
        QgsProject.instance().addMapLayer(edif_merge_layer)
        edif_merge_layer.setName('Edificacoes')
        symbol = edif_merge_layer.renderer().symbol()
        symbol.setColor(QColor.fromRgb(0,0,0))

        merge_result = processing.run("native:mergevectorlayers", {'LAYERS':imp_classes_sources,'CRS':None,'OUTPUT':'TEMPORARY_OUTPUT'})
        imp_merge_layer = merge_result['OUTPUT']
        QgsProject.instance().addMapLayer(imp_merge_layer)
        imp_merge_layer.setName('Impeditivo')
        symbol = imp_merge_layer.renderer().symbol()
        symbol.setColor(QColor.fromRgb(250,50,50))


        rest_classes_sources.append(duplicate_vectorized_layer.source())
        merge_result = processing.run("native:mergevectorlayers", {'LAYERS':rest_classes_sources,'CRS':None,'OUTPUT':'TEMPORARY_OUTPUT'})
        rest_merge_layer = merge_result['OUTPUT']

        diff_dict = processing.run("native:difference", {'INPUT':rest_merge_layer,'OVERLAY':imp_merge_layer,'OUTPUT':'TEMPORARY_OUTPUT','GRID_SIZE':None})
        rest_diff_layer = diff_dict['OUTPUT']
        QgsProject.instance().addMapLayer(rest_diff_layer)
        rest_diff_layer.setName('Restritivo')
        symbol = rest_diff_layer.renderer().symbol()
        symbol.setColor(QColor.fromRgb(250,250,0))
        
        if boolloadlayers == False:
            for classe in classes_to_remove:
                QgsProject.instance().removeMapLayer(classe)

        diff_dict = processing.run("native:difference", {'INPUT':frame_layer,'OVERLAY':imp_merge_layer,'OUTPUT':'TEMPORARY_OUTPUT','GRID_SIZE':None})
        adeq1_diff_layer = diff_dict['OUTPUT']
        diff_dict = processing.run("native:difference", {'INPUT':adeq1_diff_layer,'OVERLAY':rest_diff_layer,'OUTPUT':'TEMPORARY_OUTPUT','GRID_SIZE':None})
        adeq2_diff_layer = diff_dict['OUTPUT']
        QgsProject.instance().addMapLayer(adeq2_diff_layer)
        adeq2_diff_layer.setName('Adequado')
        symbol = adeq2_diff_layer.renderer().symbol()
        symbol.setColor(QColor.fromRgb(50,250,50))

        # QgsProject.instance().removeMapLayer(rest_diff_layer)
        canvas.freeze(False)

        return {}
    def clear_pycache(self, path):
        pycache_dir = os.path.join(path, "__pycache__")
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir)

        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".pyc"):
                    os.remove(os.path.join(root, file))
        ###############################################################################################################################