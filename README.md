# Projeto Final de Curso (PFC2023) - Mapas de Trafegabilidade para o Exército

O projeto PFC2023 foi desenvolvido por nossa equipe com o objetivo de auxiliar o Exército na geração de mapas de trafegabilidade, considerando diferentes meios de tráfego e regiões específicas na escala de 1:25000. O sistema categoriza áreas como:

- **Áreas Adequadas para Tráfego**: Regiões ideais para movimentação, sem restrições significativas.
  
- **Áreas Restritivas**: Zonas com limitações para o tráfego, como vegetação densa ou declividade moderada.
  
- **Áreas Impeditivas para Tráfego**: Regiões onde o tráfego é desaconselhado ou impossível devido a obstáculos naturais.

## Como Funciona

O projeto é baseado em um plugin para o software QGIS. Aqui está um resumo do processo:

1. **Seleção do Meio de Tráfego**: O usuário escolhe o meio de tráfego que será utilizado entre as opções:
   - Tropa a pé
   - Viaturas sobre rodas
   - Viaturas sobre lagartas

2. **Seleção do Mapa Índice (MI)**: O usuário seleciona o MI da região de interesse, considerando mapas na escala de 1:25000.

3. **Processamento dos Dados**: O plugin processa as informações, avaliando características do terreno e outros fatores relevantes.

4. **Classificação das Áreas**: As áreas são classificadas em adequadas, restritivas ou impeditivas para o meio de tráfego selecionado.

5. **Opção de Visualização**: O usuário tem a opção de visualizar não apenas o mapa final de trafegabilidade, mas também todas as camadas intermediárias que foram usadas no processo de determinação.

## Instalação e Configuração

Siga os passos abaixo para baixar e configurar o plugin no QGIS:

1. **Baixe o Plugin**: 
   - Clique [aqui](https://github.com/kaiopimentel/PFC2023/archive/main.zip) para baixar o arquivo ZIP do projeto.
   - Extraia o conteúdo do arquivo ZIP em uma pasta de sua escolha.

2. **Instale o Plugin no QGIS**:
   - Abra o QGIS.
   - Vá até o menu `Plugins` > `Manage and Install Plugins...`.
   - Clique na aba `Install from ZIP` e selecione o arquivo ZIP que você baixou.
   - Clique em `Install Plugin`.

3. **Utilize o Plugin**:
   - Após a instalação, vá até o menu `Plugins` e selecione `PFC2023`.
   - Escolha o meio de tráfego e o MI desejado.
   - Processe e visualize os resultados conforme sua necessidade.

## Contribuições

Se desejarem contribuir para este projeto ou tiverem sugestões de melhorias, sintam-se à vontade para abrir uma issue ou enviar um pull request.
