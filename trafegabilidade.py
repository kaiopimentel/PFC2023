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

import os
import sys
import inspect

from qgis.core import QgsProcessingAlgorithm, QgsApplication
from .trafegabilidade_provider import TrafegabilidadeProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class TrafegabilidadePlugin(object):

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = TrafegabilidadeProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
