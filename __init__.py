# -*- coding: utf-8 -*-
"""
/***************************************************************************
Elaboração automatizada de mapas de trafegabilidade
                                 A QGIS plugin

 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Arthur Santos/ Kaio Pimentel/ Felipe Viana'
__date__ = '2023-03-23'
__copyright__ = ''

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PontoControle class from file PontoControle.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .trafegabilidade import TrafegabilidadePlugin
    return TrafegabilidadePlugin()
