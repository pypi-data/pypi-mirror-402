"""Core processing functions for EDS map generation."""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def gerar_eds_map(caminho_csv: str, pasta_saida: str, cmap_name: str = "viridis") -> bool:
    """
    Generate EDS heatmap from CSV file.
    
    Args:
        caminho_csv: Path to input CSV file
        pasta_saida: Output directory for PNG image
        cmap_name: Matplotlib colormap name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Leitura robusta do CSV (sem cabeçalho)
        df = pd.read_csv(caminho_csv, header=None)
        df_numeric = df.apply(pd.to_numeric, errors="coerce")
        data = df_numeric.to_numpy(dtype=float)
        
        # Validação de dados
        if data.size == 0 or np.all(np.isnan(data)):
            print(f"Dados inválidos/vazios em: {caminho_csv}")
            return False

        # Extração inteligente do nome do elemento
        nome = os.path.basename(caminho_csv)
        n0 = os.path.splitext(nome)[0]
        parts = n0.split("_")
        
        if len(parts) > 1:
            elemento = parts[-1]  # Pega o último termo após "_"
            prefix = "_".join(parts[:-1])
            out_name = f"{prefix}_edsmap_{elemento}.png"
        else:
            elemento = n0
            out_name = f"edsmap_{elemento}.png"
            
        path_salvar = os.path.join(pasta_saida, out_name)

        # Plotagem
        fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
        im = ax.imshow(data, cmap=cmap_name, origin='upper', interpolation='bilinear')
        ax.set_aspect('equal')
        ax.axis('off')

        ax.set_title(f"EDS-Map - {elemento}", fontsize=26, pad=16)

        cbar = fig.colorbar(im, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
        cbar.set_label("Intensidade", fontsize=22)
        cbar.ax.tick_params(labelsize=18)

        plt.tight_layout()
        fig.savefig(path_salvar, dpi=300, bbox_inches="tight")
        plt.close(fig)  # Libera memória
        return True
    
    except Exception as e:
        print(f"Erro ao processar {caminho_csv}: {e}")
        return False


# Available colormaps
COLORMAP_OPTIONS = [
    "Blues", "viridis", "magma", "inferno", "plasma", "cividis",
    "Greys", "Reds", "Greens", "Oranges", "Purples", "turbo",
    "Spectral", "coolwarm", "seismic", "jet"
]
