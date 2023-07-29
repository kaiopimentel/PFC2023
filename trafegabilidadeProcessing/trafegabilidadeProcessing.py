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

import os
from osgeo import gdal
from qgis.PyQt.QtCore import QCoreApplication, QVariant
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
                       QgsColorRampShader,
                       QgsRasterShader,
                       QgsSingleBandPseudoColorRenderer, 
                       QgsColorRampShader, 
                       QgsRasterShader
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
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    MI = 'MI'
    TYPE = 'TYPE'
    FRAME = 'FRAME'
    CRS = 'CRS' 
    SLOPE = 'SLOPE'
    MaxSlope = 'MaxSlope'
    MapaTematico = 'MapaTematico'
    SITUATION = 'SITUATION'

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

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Camada de Entrada'),
                [QgsProcessing.TypeVectorAnyGeometry],
                optional = True
            )
        )
        
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
                ['Viatura sobre rodas', 'Viatura sobre lagartas', 'Deslocamento a pé']
            )

        )
        self.addParameter(
            QgsProcessingParameterString(
                self.MaxSlope,
                self.tr('Declividade máxima permitida para trajeto'),
                optional = True
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
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.FRAME,
                self.tr('Moldura')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output Raster')
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.SLOPE,
                self.tr('Output Slope')
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.MapaTematico,
                self.tr('Output Mapa Temático')
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

        if situation == 0:
            #vtr sobre rodas
            max_slope=17
        elif situation == 1:
            #vtr sobre lagartas
            max_slope=26
        elif situation == 2:
            #tropa a pé
            max_slope=30
        ###############################################################################################################################
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

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.FRAME,
            context,
            Fields,
            GeomType,
            crs
        )

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
        # feedback.pushInfo('INOM: {}'.format(inom))
        # feedback.pushInfo('MI: {}'.format(mi))
        feat.setGeometry(geom)
        feat.setAttributes(att)
        sink.addFeature(feat, QgsFeatureSink.FastInsert)

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.FRAME))

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

        dem_url = f'https://portal.opentopography.org/API/globaldem?demtype={dem_code}&south={south}&north={north}&west={west}&east={east}&outputFormat=GTiff'
        dem_url=dem_url + "&API_Key=" + parameters['API_key']

        dem_file = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        try:
            # Download file
            alg_params = {
                'URL': dem_url,
                'OUTPUT': dem_file
            }
            outputs['DownloadFile'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        except:
            response = requests.request("GET", dem_url, headers={}, data={})
            
            raise QgsProcessingException (response.text.split('<error>')[1][:-8])
        
        # Load layer into project
        dem_file_name = os.path.basename(dem_file)
        if dem_file_name == 'OUTPUT.tif':
            alg_params = {           
                'INPUT': dem_file,
                'NAME': dem_code+"[Memory]"
            }
        else:
            alg_params = {           
                'INPUT': dem_file,
                'NAME': dem_file_name
            }

        ###############################################################################################################################

        # Substitua as seguintes strings com o nome da camada e o caminho de saída

        raster_path = outputs["DownloadFile"]["OUTPUT"]

        
        raster_layer = QgsRasterLayer(raster_path, f'MDE_{nome}')
        if not raster_layer.isValid():
            feedback.pushInfo(f'Erro ao carregar o raster: {raster_layer.lastError().message()}')
        else:
            # Adiciona a camada raster ao projeto do QGIS
            QgsProject.instance().addMapLayer(raster_layer) 

        ############################################################ Descobrir Fuso UTM

        ponto_central = get_raster_center_point(dem_file)

        point_x = ponto_central.x()
        point_y = ponto_central.y()
        
        utm_zone = get_zone_number(point_y, point_x)

        if point_y <= 0:
            south_hemisphere = True
        else:
            south_hemisphere = False

        crs = CRS.from_dict({'proj': 'utm', 'zone': utm_zone[0:2], 'south': south_hemisphere})
        epsg = crs.to_authority()

        # feedback.pushInfo(f'{epsg[1]}')

        ############################################################ Reprojetar
        
        reproj_dict = processing.run("gdal:warpreproject", {'INPUT':dem_file,'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:4326'),'TARGET_CRS':QgsCoordinateReferenceSystem(f'EPSG:{epsg[1]}'),'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':30,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OUTPUT':'TEMPORARY_OUTPUT'})
        feedback.pushInfo(f'{type(reproj_dict)}')
        feedback.pushInfo(f'{reproj_dict}')

        reproj_path = reproj_dict['OUTPUT']
        reproj_raster = QgsRasterLayer(reproj_path, f'REPROJ_{nome}')
        QgsProject.instance().addMapLayer(reproj_raster)
        ############################################################ Cálculo Declividade
        
        slope_dict = processing.run("native:slope", {'INPUT':reproj_path,'Z_FACTOR':1,'OUTPUT':'TEMPORARY_OUTPUT'})
        slope_path = slope_dict['OUTPUT']
        slope_raster = QgsRasterLayer(slope_path, f'SLOPE_{nome}')
        QgsProject.instance().addMapLayer(slope_raster)
        
        ############################################################ Mapa Temático
        # max_slope = float(parameters[self.MaxSlope])
        formula = f'(A < {max_slope}) * 1 + (A >= {max_slope}) * 0'

        thematic_dict = processing.run("gdal:rastercalculator", {
            'INPUT_A': slope_path, 'BAND_A': 1,
            'INPUT_B': None, 'BAND_B': -1,
            'INPUT_C': None, 'BAND_C': -1,
            'INPUT_D': None, 'BAND_D': -1,
            'INPUT_E': None, 'BAND_E': -1,
            'INPUT_F': None, 'BAND_F': -1,
            'FORMULA': formula,
            'NO_DATA': None,
            'RTYPE': 5,
            'OPTIONS': '',
            'EXTRA': '',
            'OUTPUT': parameters[self.MapaTematico]
        })

        thematic_raster_path = thematic_dict['OUTPUT']

        # Defina o estilo de cores contínuas
        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
        color_ramp.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(0, QColor(255, 0, 0)),
            QgsColorRampShader.ColorRampItem(1, QColor(0, 255, 0))
        ])

        shader = QgsRasterShader()
        shader.setRasterShaderFunction(color_ramp)

        thematic_raster = QgsRasterLayer(thematic_raster_path, f'MapaTematico_{nome}')
        renderer = QgsSingleBandPseudoColorRenderer(thematic_raster.dataProvider(), 1, shader)
        thematic_raster.setRenderer(renderer)

        QgsProject.instance().addMapLayer(thematic_raster)
        import requests
        import tempfile
        from qgis.PyQt.QtCore import QUrl
        from qgis.core import QgsVectorLayer, QgsProject, QgsProcessingUtils, QgsMessageLog, Qgis

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

        # Build WFS request URL
        params = {
            "service": "WFS",
            "request": "GetFeature",
            "typeName": "ms:Trecho_Massa_Dagua_A",
            "srsName": "EPSG:4326",
            "bbox": bbox,
            "outputFormat": "GML2",  # Changed to GML2
            "version": "1.0.0",  # Added version parameter
        }
        wfs_url = "https://bdgex.eb.mil.br/ms250"
        response = requests.get(wfs_url, params=params)
        print(response.content)

        # Check if the request was successful
        if response.status_code != 200:
            QgsMessageLog.logMessage(f"Request failed with status code: {response.status_code}", 'Mapa de Trafegabilidade', level=Qgis.Critical)
            raise ValueError(f"Request failed with status code: {response.status_code}")

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
        QgsMessageLog.logMessage("Temporary file created at:" + temp_file.name, 'Mapa de Trafegabilidade', level=Qgis.Info)
        temp_file.close()

        # Write the response to a temporary GML file
        with open(temp_file.name, "w") as f:
            f.write(response.text)

        # Load the temporary GML file as a vector layer
        vector_layer = QgsVectorLayer(temp_file.name, "Trecho_Massa_Dagua_A", "ogr")
        # Set the coordinate reference system to EPSG:4326
        crs = QgsCoordinateReferenceSystem("EPSG:4326")
        vector_layer.setCrs(crs)

        # Check if the vector layer is valid
        if not vector_layer.isValid():
            QgsMessageLog.logMessage(vector_layer.error().message(), 'Mapa de Trafegabilidade', level=Qgis.Critical)  # DEBUG: print the error message
            raise ValueError("Vector layer failed to load!")

        # Add the vector layer to the project
        QgsProject.instance().addMapLayer(vector_layer)

        return {}
        ###############################################################################################################################