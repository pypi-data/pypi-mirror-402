"""GUI application for EDSMapPlotter."""
import os
import sys
import tkinter as tk
from tkinter import filedialog, MULTIPLE, messagebox
from PIL import Image, ImageTk
import ctypes

from .core import gerar_eds_map, COLORMAP_OPTIONS

# --- Configuração de High DPI (Melhora nitidez no Windows) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# --- Tentativa de Importar Drag-and-Drop ---
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False


def resource_path(relative_path):
    """Obtém caminho absoluto para recursos (imagens), funciona em dev e PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def run_gui():
    """Launch the EDSMapPlotter GUI application."""
    # Definição dos Arquivos de Ícone
    ICON_PNG = resource_path(os.path.join("resources", "EDSMapPlotter_icon.png"))
    ICON_ICO = resource_path(os.path.join("resources", "EDSMapPlotter_icon.ico"))
    
    # Inicializa Janela (com ou sem DnD)
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
        messagebox.showinfo("Aviso", "Biblioteca Drag-and-Drop não encontrada.\\nUse o botão 'Selecionar Arquivos'.")

    root.title("EDSMapPlotter v0.2.1")
    root.geometry("620x680")

    # Tenta carregar ícone da janela (.ico no Windows fica melhor)
    try:
        if os.name == 'nt' and os.path.exists(ICON_ICO):
            root.iconbitmap(ICON_ICO)
        elif os.path.exists(ICON_PNG):
            icon = tk.PhotoImage(file=ICON_PNG)
            root.iconphoto(False, icon)
    except Exception:
        pass

    # --- Interface Gráfica ---
    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    # Logo no topo
    try:
        if os.path.exists(ICON_PNG):
            img = Image.open(ICON_PNG).resize((110, 110), Image.Resampling.LANCZOS)
            tklogo = ImageTk.PhotoImage(img)
            lbl_logo = tk.Label(main_frame, image=tklogo)
            lbl_logo.image = tklogo
            lbl_logo.pack(pady=(0, 15))
    except Exception:
        pass

    # Área de Lista
    tk.Label(main_frame, text="Arquivos CSV Selecionados:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    
    list_frame = tk.Frame(main_frame)
    list_frame.pack(fill="x", pady=5)
    
    scrollbar = tk.Scrollbar(list_frame, orient="vertical")
    lista = tk.Listbox(list_frame, selectmode=MULTIPLE, height=8, yscrollcommand=scrollbar.set, 
                      bg="#f8f9fa", font=("Consolas", 9))
    scrollbar.config(command=lista.yview)
    
    scrollbar.pack(side="right", fill="y")
    lista.pack(side="left", fill="x", expand=True)

    # Lógica da Lista
    def add_files(filepaths):
        exist = set(lista.get(0, tk.END))
        count_new = 0
        for p in filepaths:
            # Remove chaves {} que o TkDnD às vezes coloca no Windows
            p = p.strip("{}")
            if p not in exist and p.lower().endswith(".csv"):
                lista.insert(tk.END, p)
                count_new += 1
        lbl_status.config(text=f"{count_new} arquivos adicionados.", fg="#0056b3")

    def sel():
        paths = filedialog.askopenfilenames(filetypes=[("Arquivos CSV", "*.csv")])
        add_files(paths)

    def rem():
        sel_items = list(lista.curselection())
        for i in reversed(sel_items):
            lista.delete(i)
        lbl_status.config(text=f"{len(sel_items)} arquivos removidos.", fg="#dc3545")

    # Botões de Controle da Lista
    btn_frame = tk.Frame(main_frame)
    btn_frame.pack(fill="x", pady=5)
    tk.Button(btn_frame, text="📂 Adicionar CSVs", command=sel, width=18).pack(side="left", padx=5)
    tk.Button(btn_frame, text="❌ Remover Seleção", command=rem, width=18).pack(side="right", padx=5)

    # Configuração de Saída
    tk.Label(main_frame, text="Salvar Imagens em:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(20, 0))
    
    out_frame = tk.Frame(main_frame)
    out_frame.pack(fill="x", pady=5)
    out_entry = tk.Entry(out_frame)
    out_entry.pack(side="left", fill="x", expand=True)
    
    def sel_out():
        d = filedialog.askdirectory()
        if d:
            out_entry.delete(0, tk.END)
            out_entry.insert(0, d)
    
    tk.Button(out_frame, text="...", command=sel_out, width=4).pack(side="right", padx=5)

    # Seletor de Cores
    tk.Label(main_frame, text="Esquema de Cores (Colormap):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 0))
    cmap_var = tk.StringVar(value="viridis")
    opt = tk.OptionMenu(main_frame, cmap_var, *COLORMAP_OPTIONS)
    opt.config(width=25)
    opt.pack(anchor="w", pady=5)

    # Barra de Status
    lbl_status = tk.Label(main_frame, text="Pronto para iniciar.", bd=1, relief=tk.SUNKEN, 
                         anchor="w", fg="#666")
    lbl_status.pack(side="bottom", fill="x", pady=(20, 0))

    # Processamento Principal
    def process():
        files = lista.get(0, tk.END)
        folder = out_entry.get().strip()
        
        if not files:
            messagebox.showwarning("Atenção", "Nenhum arquivo CSV foi selecionado.")
            return
        if not folder:
            messagebox.showwarning("Atenção", "Por favor, selecione a pasta onde as imagens serão salvas.")
            return
            
        os.makedirs(folder, exist_ok=True)
        lbl_status.config(text="Processando... Isso pode levar alguns segundos.", fg="#e67e22")
        root.update()  # Atualiza a tela imediatamente
        
        sucessos = 0
        erros = 0
        
        for f in files:
            ok = gerar_eds_map(f, folder, cmap_var.get())
            if ok:
                sucessos += 1
            else:
                erros += 1
        
        lbl_status.config(text=f"Finalizado: {sucessos} mapas gerados com sucesso.", fg="#28a745")
        
        msg = f"Processamento concluído!\\n\\n✅ Sucessos: {sucessos}\\n❌ Erros: {erros}\\n\\nImagens salvas em:\\n{folder}"
        messagebox.showinfo("Relatório", msg)

    # Botão Gigante de Ação
    tk.Button(main_frame, text="GERAR MAPAS", command=process, bg="#28a745", fg="white",
              font=("Segoe UI", 12, "bold"), height=2, cursor="hand2").pack(fill="x", pady=25)

    # Drag and Drop Bindings
    if HAS_DND:
        def drop(event):
            raw_data = event.data
            if raw_data.startswith("{") and "}" in raw_data:
                paths = root.tk.splitlist(raw_data)
            else:
                paths = raw_data.split()
            add_files(paths)

        lista.drop_target_register(DND_FILES)
        lista.dnd_bind('<<Drop>>', drop)

    root.mainloop()
