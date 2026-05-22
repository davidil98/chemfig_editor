import os
import subprocess
import shutil
import sys

# --- CONFIGURACIÓN DE RUTAS ---
# Ajusta esto a la carpeta real donde quieras guardar las imágenes finales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, '..', 'assets', 'steps')
BASE_TEMP_NAME = "temp_structure"

def check_dependencies():
    """Verifica si las herramientas externas necesarias están instaladas."""
    dependencies = ['pdflatex', 'pdftoppm']
    missing = []
    for dep in dependencies:
        if shutil.which(dep) is None:
            missing.append(dep)
    
    if missing:
        print("❌ Error: Faltan dependencias críticas en el sistema.")
        print(f"Por favor instala: {', '.join(missing)}")
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            print("En Linux/macOS suele requerir: texlive-full (o similar) y poppler-utils.")
        elif sys.platform.startswith('win'):
            print("En Windows suele requerir: MiKTeX (o TeX Live) y Poppler para Windows añadido al PATH.")
        sys.exit(1)

def compile_latex_to_png(latex_content, output_filename):
    """Compila contenido LaTeX con ChemFig, lo convierte a PNG y limpia."""
    
    tex_file = f"{BASE_TEMP_NAME}.tex"
    pdf_file = f"{BASE_TEMP_NAME}.pdf"
    
    # 1. Crear el archivo .tex temporal
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)

    print(f"⌛ Generando {output_filename}...")

    try:
        # 2. Compilar PDF (standalone garantiza borde mínimo)
        subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_file], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_file], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Convertir PDF a PNG de alta calidad (300 dpi)
        # -singlefile genera 'temp_structure.png' directamente
        subprocess.run(['pdftoppm', '-png', '-r', '300', '-singlefile', pdf_file, BASE_TEMP_NAME], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 4. Mover al directorio de destino final
        generated_png = f"{BASE_TEMP_NAME}.png"
        final_path = os.path.join(OUTPUT_DIR, output_filename)
        shutil.move(generated_png, final_path)
        print(f"Imagen guardada en: {final_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error compilando {output_filename}. Revisa tu instalación de LaTeX/ChemFig.")
        # Opcional: no borrar el .log si falla para debug
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        # 5. Limpieza estricta de archivos auxiliares
        for ext in ['.aux', '.log', '.tex', '.pdf', '.png']:
            temp_file = f"{BASE_TEMP_NAME}{ext}"
            if os.path.exists(temp_file):
                os.remove(temp_file)

def save_question_steps(latex_content, output_filename):
    """Guarda los pasos en la carpeta de instrucciones, como bitácora."""
    output_dir = os.path.join(OUTPUT_DIR, "..", "instructions_latex")

    # Crear el directorio de salida si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(os.path.join(output_dir, output_filename), 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
# --- PLANTILLA BASE LATEX ---
steps_list = []
LATEX_HEADER = r"""
\documentclass[border=15pt]{standalone}
\usepackage{chemfig}
\usepackage{mhchem}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\usetikzlibrary{calc}
\usepackage{xcolor}
\definecolor{armygreen}{rgb}{0.29, 0.33, 0.13}
\definecolor{antiquefuchsia}{rgb}{0.57, 0.36, 0.51}
% Configuración global de ChemFig para proyecciones de Fischer limpias
\setchemfig{atom sep=2em, bond offset=1pt, angle increment=45}
\begin{document}
"""
LATEX_FOOTER = r"\end{document}"

latex_paso0 = LATEX_HEADER + r"""
\schemestart
    \chemname{\chemfig{*6(=-=(-(=[2]@{Oatm1}O)-[@{Obnd2}:-30]O-[@{Obnd3}:60]@{Oatm3}O-[@{Hbnd}::30]@{Hatm}H)-=(-Cl)-)}}{mCPBA}
    \arrow(--[yshift=3pt]){0}[,0]\+
    \chemfig{*6(@{Cdbnd}-----=[@{dbnd}])}
    \arrow{->}
    %\chemfig{*3(-O-(*6(------)))}
    \chemfig[bond style={line width=0.6pt}]{*6(--(-[:35]O?)-?---)}
    \+{,,4mm}
    \chemfig{*6(=-=(-(=[2]O)-[:-30]OH)-=(-Cl)-)}
\schemestop
\chemmove{
    \draw[-stealth,thin,shorten <=5pt,dash pattern= on 2pt off 2pt,blue]
    (Obnd3).. controls +(110:5mm) and +(90:5mm)..(Obnd2);
    \draw[-stealth,thin,shorten <=5pt,dash pattern= on 2pt off 2pt,blue]
    (Oatm1).. controls +(90:5mm) and +(110:5mm)..(Hatm);
    \draw[-stealth,thin,shorten <=5pt,dash pattern= on 2pt off 2pt,blue]
    (Hbnd).. controls +(0:5mm) and +(180:5mm)..(dbnd);
    \draw[-stealth,thin,shorten <=5pt,dash pattern= on 2pt off 2pt,blue]
    (Cdbnd).. controls +(185:5mm) and +(0:5mm)..(Oatm3);
}
""" + LATEX_FOOTER
steps_list.append(latex_paso0)

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    check_dependencies()
    
    # Asegurar que el directorio de salida existe
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"Directorio creado: {OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creando el directorio {OUTPUT_DIR}: {e}")
            sys.exit(1)

    problem_id = "20878"
    for i, step in enumerate(steps_list):
        compile_latex_to_png(step, f"problem{problem_id}_step{i+1}.png")
        save_question_steps(step, f"problem{problem_id}_step{i+1}.tex")
    
    print("\nProceso finalizado.")