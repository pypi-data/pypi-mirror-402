# EDSMapPlotter

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fdossi/EDSMapPlotter/blob/main/EDSMapPlotter_Colab.ipynb)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17741072.svg)](https://doi.org/10.5281/zenodo.17741072)
![License](https://img.shields.io/github/license/fdossi/EDSMapPlotter)
![Release](https://img.shields.io/github/v/release/fdossi/EDSMapPlotter)

**EDSMapPlotter** é uma ferramenta open-source para automatizar a geração de mapas a partir de dados brutos (CSV) de Espectroscopia de Energia Dispersiva (EDS/EDX).

O software converte matrizes numéricas (arquivos `.csv` exportados de microscópios SEM) em imagens de alta resolução (300 DPI) prontas para publicação científica.

---

## 🚀 Como Usar

### Opção A: Executar na Nuvem (Google Colab)
Não requer instalação. Ideal para uso rápido ou em computadores sem Python configurado.
1. Clique no selo **"Open in Colab"** acima.
2. Faça upload dos seus CSVs.
3. Baixe os mapas gerados automaticamente.

### Opção B: Instalação via PyPI (Recomendado)
Instale diretamente do Python Package Index:
```bash
pip install edsmapplotter
```

Execute o programa:
```bash
edsmapplotter
```

### Opção C: Instalação Local (Desenvolvedor)
Para usar a interface gráfica (GUI) com suporte a arrastar-e-soltar no Windows/Linux/Mac:

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o script:
   ```bash
   python EDSMapPlotter.py
   ```

## Funcionalidades

**Processamento em Lote**: Arraste dezenas de arquivos CSV e converta todos de uma vez.

**Detecção Automática de Elementos**: O script lê o nome do arquivo (ex: Area1_Fe.csv) e nomeia o gráfico corretamente ("Fe").

**Visualização**: Suporte a múltiplos mapas de cores (Viridis, Inferno, Blues, Reds, etc.).

**Alta Qualidade**: Exportação fixa em 300 DPI.

## Formato de Entrada
O software espera arquivos .csv contendo apenas a matriz de intensidades (sem cabeçalhos/headers de texto), que é o padrão de exportação de muitos softwares de microanálise.

## Citação

Se utilizar esta ferramenta em sua pesquisa, por favor cite:

Dossi, F. (2025). *EDSMapPlotter: A Python tool for EDS map visualization* (Version v0.2.1) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.17741072
