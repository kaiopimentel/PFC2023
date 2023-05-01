# PFC2023
Elaboração de mapas de trafegabilidade de elementos de combate da Força Terrestre (materiais e pessoal) de modo automático e no QGIS, considerando parâmetros de deslocamento pré-definidos.

## Na pasta calculo_declividade, temos um código que funciona da seguinte forma:

1. Importa as bibliotecas necessárias: `os` (manipulação de arquivos), `numpy` (cálculos numéricos), `gdal` (manipulação de dados geoespaciais) e `qgis.core` (funções do QGIS).

2. Define a função `calculate_slope(raster_layer, output_path)`, que recebe dois parâmetros: `raster_layer` (uma camada raster carregada no QGIS) e `output_path` (o caminho do arquivo de saída que será gerado).

3. A função começa abrindo o arquivo raster usando a função `gdal.Open()` e obtém a banda (neste caso, a primeira banda) e a matriz de transformação geoespacial (GeoTransform).

4. A matriz de elevação é lida como uma matriz NumPy usando a função `ReadAsArray()` e as resoluções x e y são extraídas da matriz GeoTransform.

5. A declividade é calculada usando a função NumPy `gradient()` para calcular as derivadas parciais em relação aos eixos x e y, e depois aplicando a fórmula de declividade que leva em conta as resoluções x e y. O resultado é convertido em graus usando a função `arctan()` e a constante `np.pi`.

6. Um novo arquivo raster é criado para armazenar os dados de declividade. Ele usa o mesmo tamanho, projeção e matriz GeoTransform que o arquivo de entrada.

7. Caso não seja possível criar o arquivo de saída, a função exibe uma mensagem de erro e retorna.

8. Os dados de declividade são escritos no arquivo de saída usando a função `WriteArray()` e o valor "no data" é configurado como -9999.

9. A função termina fechando o arquivo de saída e liberando recursos.

10. Fora da função, o nome da camada de entrada e o caminho do arquivo de saída são definidos. Em seguida, a camada de entrada é carregada no QGIS usando a função `QgsProject.instance().mapLayersByName()`.

11. A função `calculate_slope()` é chamada com a camada de entrada e o caminho do arquivo de saída.

12. A camada de declividade é carregada no QGIS usando a função `QgsRasterLayer()` e adicionada ao projeto com a função `QgsProject.instance().addMapLayer()`.

## Em relação ao cálculo de declividade:

O gradiente é uma medida da taxa de variação de uma função em relação às suas variáveis independentes. No caso da declividade, a função é a elevação, e as variáveis independentes são as coordenadas x e y. O gradiente é um vetor que aponta na direção de maior aumento de elevação e tem magnitude igual à taxa de variação de elevação nessa direção. 

Ao calcular a declividade, estamos interessados na taxa de variação da elevação em relação às coordenadas x e y. Para isso, utilizamos a função `np.gradient()` do NumPy, que retorna as derivadas parciais da matriz de elevação em relação a cada eixo. Essas derivadas parciais nos dão as taxas de variação de elevação em relação às coordenadas x e y, respectivamente. 

A função `np.gradient()` retorna duas matrizes: uma para a derivada parcial em relação ao eixo x (leste-oeste) e outra para a derivada parcial em relação ao eixo y (norte-sul). Para encontrar a taxa de variação da elevação em cada ponto do terreno, combinamos essas duas derivadas parciais usando o teorema de Pitágoras, que nos dá a magnitude do gradiente:

magnitude = sqrt((derivada parcial em relação a x)² + (derivada parcial em relação a y)²)

No entanto, o valor da magnitude do gradiente não é a declividade em si. A declividade é o ângulo entre o plano tangente à superfície do terreno em um ponto e um plano horizontal. Podemos calcular esse ângulo usando a tangente inversa (arco tangente) da magnitude do gradiente, como segue:

declividade = arctan(magnitude)

Por fim, convertemos o ângulo de declividade de radianos para graus, multiplicando por (180 / π). Assim, obtemos a declividade do terreno em graus para cada ponto da matriz de elevação.
