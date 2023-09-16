# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Elaboração automatizada de mapas de trafegabilidade
                                 A QGIS plugin
 
                              -------------------
        begin                : 2023-03-23
        email                : arthur.santos@eb.mil.br/ kaio.pimentel@eb.mil.br/ felipe.silva@ime.eb.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import sys
sys.dont_write_bytecode = True
__author__ = 'Arthur Santos/ Kaio Pimentel/ Felipe Viana'
__date__ = '2023-03-23'
__copyright__ = ''

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from .trafegabilidadeProcessing.trafegabilidadeProcessing import TrafegabilidadeProcessingAlgorithm

class TrafegabilidadeProvider(QgsProcessingProvider):
    '''
    Provider do handle the algorithms
    '''
    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(TrafegabilidadeProcessingAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'providerTrafegabilidade'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return self.tr('PFC 2023')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
