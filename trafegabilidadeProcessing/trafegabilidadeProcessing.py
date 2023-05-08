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
import sys
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterCrs,
                       QgsApplication,
                       QgsProcessingContext,
                       QgsProcessingFeedback,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsPointXY,
                       QgsFeature,
                       QgsGeometry)
from qgis import processing

from numpy import array
from .cartography import reprojectPoints, mi2inom, inom2mi

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
    LOC = QgsApplication.locale()[:2]   

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
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('SRC da Moldura')
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
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        
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

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        # if source is None:
        #     raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        # (sink, dest_id) = self.parameterAsSink(
        #     parameters,
        #     self.OUTPUT,
        #     context
        #     # source.fields(),
        #     # source.wkbType(),
        #     # source.sourceCrs()
        # )
        
        # context_aux = QgsProcessingContext()
        # crs_aux = QgsCoordinateReferenceSystem(4326)
        
        # feedback_aux = QgsProcessingFeedback()

        # inom2utm_parameters = {'NAME':mi, 'TYPE':0, 'CRS':crs, 'FRAME':'TEMPORARY_OUTPUT'}
        # feedback.pushInfo(f'{inom2utm_parameters}')
        # GridDownload = Inom2utmGrid()
        # GridDownload.processAlgorithm(parameters=inom2utm_parameters, context=context_aux, feedback=feedback_aux)

        ###############################################################################################################################
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
            feedback.pushInfo(self.tr('Origem')+': Longitude = {} e Latitude = {}'.format(lon, lat))
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
        feedback.pushInfo('INOM: {}'.format(inom))
        feedback.pushInfo('MI: {}'.format(mi))
        feat.setGeometry(geom)
        feat.setAttributes(att)
        sink.addFeature(feat, QgsFeatureSink.FastInsert)

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.FRAME))

        feedback.pushInfo(self.tr('Operação finalizada com sucesso!'))
        feedback.pushInfo(self.tr('Leandro França - Eng Cart'))

        return {self.FRAME: dest_id}
        ###############################################################################################################################
        
        # Send some information to the user
        # feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        # if sink is None:
        #     raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        # total = 100.0 / source.featureCount() if source.featureCount() else 0
        # features = source.getFeatures()

        # for current, feature in enumerate(features):
        #     # Stop the algorithm if cancel button has been clicked
        #     if feedback.isCanceled():
        #         break

        #     # Add a feature in the sink
        #     sink.addFeature(feature, QgsFeatureSink.FastInsert)

        #     # Update the progress bar
        #     feedback.setProgress(int(current * total))

        # To run another Processing algorithm as part of this algorithm, you can use
        # processing.run(...). Make sure you pass the current context and feedback
        # to processing.run to ensure that all temporary layer outputs are available
        # to the executed algorithm, and that the executed algorithm can send feedback
        # reports to the user (and correctly handle cancellation and progress reports!)
        if False:
            buffered_layer = processing.run("native:buffer", {
                'INPUT': dest_id,
                'DISTANCE': 1.5,
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
            }, context=context, feedback=feedback)['OUTPUT']

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}
