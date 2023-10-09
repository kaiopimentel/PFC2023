import datetime
layout_width = 300

# Lista das camadas desejadas
desired_layers = ["Trecho_Rodoviario", "Edificacoes", "Impeditivo", "Restritivo", "Adequado", "Google Satellite"]

# Garantir que todas as camadas desejadas estejam visíveis e sem restrições de escala
layers = []
for layer_name in desired_layers:
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    layer.setMinimumScale(0)  # Desativar a escala mínima
    layer.setMaximumScale(1e9)  # Desativar a escala máxima
    layers.append(layer)
    QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(True)

# 1. Criar um novo layout de impressão
project = QgsProject.instance()
manager = project.layoutManager()

# Nome único para evitar conflitos
layout_name = 'Trafegabilidade ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(layout_name)
manager.addLayout(layout)

# 2. Adicionar item de mapa maior e centralizado
map = QgsLayoutItemMap(layout)
map.setRect(5, 30, 290, 180)  # Ajuste inicial de posição e dimensões

layout.addLayoutItem(map)  # Adicione o mapa ao layout primeiro

# Ajuste a posição do mapa usando attemptMove
map.attemptMove(QgsLayoutPoint(5, 20, QgsUnitTypes.LayoutMillimeters))

# Ajustar a extensão do mapa para preencher o item de layout
canvas = iface.mapCanvas()
map.setExtent(canvas.extent())

# Configurar a ordem das camadas
map.setLayers(layers)

layout.addLayoutItem(map)
# 3. Adicionar título com fonte maior, ajuste de margem, borda e tamanho adequado
title = QgsLayoutItemLabel(layout)
title.setText("Mapa de Trafegabilidade")
font = QFont("Arial", 24)  # Define a fonte
title.setFont(font)  # Ajusta o tamanho da fonte
title.adjustSizeToText()  # Ajusta o tamanho da caixa ao texto
title.setFrameEnabled(True)  # Adiciona borda
title.setFrameStrokeWidth(QgsLayoutMeasurement(1, QgsUnitTypes.LayoutMillimeters))  # Ajusta a largura da borda
title.setHAlign(Qt.AlignCenter)  # Centraliza o texto horizontalmente
title.setReferencePoint(QgsLayoutItem.UpperMiddle)
title.attemptMove(QgsLayoutPoint(150, 0, QgsUnitTypes.LayoutMillimeters))  # Ajuste de posição

# Calcula a altura do texto e ajusta o tamanho vertical da caixa do título
font_metrics = QFontMetrics(font)
title_height = font_metrics.boundingRect(title.text()).height() / 3.6  # Obtém a altura do texto em milímetros
title.attemptResize(QgsLayoutSize(100, title_height + 5, QgsUnitTypes.LayoutMillimeters))  # Ajuste no tamanho vertical com uma pequena margem
layout.addLayoutItem(title)


# 4. Adicionar escala ajustada, centralizada, com borda, maior e mais acima
scale_bar = QgsLayoutItemScaleBar(layout)
scale_bar.setLinkedMap(map)
scale_bar.setStyle('Single Box')  # Estilo de barra
scale_bar.setUnits(QgsUnitTypes.DistanceMeters)  # Define as unidades
scale_bar.setUnitLabel(" m")  # Define a unidade como metros
scale_bar.setNumberOfSegments(3)  # Aumenta o número de segmentos
scale_bar.setUnitsPerSegment(3000)  # Mantém a unidade por segmento
scale_bar.setFrameEnabled(True)  # Adiciona borda
scale_bar.setFrameStrokeWidth(QgsLayoutMeasurement(1, QgsUnitTypes.LayoutMillimeters))  # Ajusta a largura da borda
scale_bar.setHeight(7)  # Ajusta a altura da escala
scale_bar.update()
scale_bar_width = scale_bar.rect().width() / 3.6
scale_bar_x_position = (layout_width - scale_bar_width) / 2
scale_bar.attemptMove(QgsLayoutPoint(95, 195, QgsUnitTypes.LayoutMillimeters))  # Ajuste na posição para ficar ainda mais acima no layout
layout.addLayoutItem(scale_bar)



# 5. Adicionar seta de orientação
north_arrow = QgsLayoutItemPicture(layout)
north_arrow.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
north_arrow.setLinkedMap(map)
north_arrow.setNorthMode(QgsLayoutItemPicture.GridNorth)  # Isso define a seta para seguir o Grid North
north_arrow.attemptResize(QgsLayoutSize(20, 20, QgsUnitTypes.LayoutMillimeters))
north_arrow.attemptMove(QgsLayoutPoint(270, 35, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(north_arrow)

# 6. Adicionar legenda ajustada, com título centralizado e sem a camada de satélite
legend = QgsLayoutItemLegend(layout)
legend.setTitle("LEGENDA")
legend.setTitleAlignment(Qt.AlignCenter)  # Centraliza o título
legend.setReferencePoint(QgsLayoutItem.LowerLeft)
legend.attemptMove(QgsLayoutPoint(10, 205, QgsUnitTypes.LayoutMillimeters))  # Ajuste na posição (subindo a legenda)
legend.setAutoUpdateModel(True)
legend.setFrameEnabled(True)  # Adiciona borda
legend.setFrameStrokeWidth(QgsLayoutMeasurement(1, QgsUnitTypes.LayoutMillimeters))  # Ajusta a largura da borda
legend.adjustBoxSize()  # Ajusta o tamanho da caixa da legenda ao conteúdo
# Remover a camada Google Satellite da legenda
root_group = QgsLayerTree()
for layer in layers:
    if layer.name() != "Google Satellite":
        root_group.addLayer(layer)
legend.model().setRootGroup(root_group)
layout.addLayoutItem(legend)

map.refresh()
layout.refresh()