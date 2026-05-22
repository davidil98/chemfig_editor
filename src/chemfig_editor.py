import os
import subprocess
import shutil
import asyncio
from pathlib import Path
from nicegui import ui, app

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

assets_dir = os.path.join(ROOT_DIR, 'assets')
os.makedirs(assets_dir, exist_ok=True)
app.add_static_files('/assets', assets_dir)

# --- ESTADO GLOBAL ---
state = {
    'auto_preview': False,
    'last_code': '',
    'header': r"""\documentclass[border=15pt]{standalone}
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
""",
    'footer': r"\end{document}"
}

def check_dependencies():
    missing = [dep for dep in ['pdflatex', 'pdftoppm'] if shutil.which(dep) is None]
    return missing

async def compile_latex(latex_body, filename="preview.png", out_dir="assets/structures", save_tex=False, tex_filename="structure.tex"):
    temp_dir = os.path.join(BASE_DIR, "temp_editor")
    os.makedirs(temp_dir, exist_ok=True)

    tex_file = "temp_preview.tex"
    pdf_file = "temp_preview.pdf"
    png_temp = "temp_preview.png"

    tex_path = os.path.join(temp_dir, tex_file)

    full_content = state['header'] + latex_body + "\n" + state['footer']

    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(full_content)

    logs = []
    success = False

    try:
        # 1. Compilar PDF (doble pasada para tikz)
        for _ in range(2):
            proc = await asyncio.create_subprocess_exec(
                'pdflatex', '-interaction=nonstopmode', tex_file,
                cwd=temp_dir,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, _ = await proc.communicate()
            logs.append(out.decode('utf-8', errors='replace'))

        if proc.returncode != 0:
            return False, logs, None, None

        # 2. PDF a PNG
        proc2 = await asyncio.create_subprocess_exec(
            'pdftoppm', '-png', '-r', '300', '-singlefile', pdf_file, "temp_preview",
            cwd=temp_dir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out2, _ = await proc2.communicate()
        if proc2.returncode == 0:
            success = True

            final_out_dir = os.path.join(ROOT_DIR, out_dir) if not os.path.isabs(out_dir) else out_dir
            os.makedirs(final_out_dir, exist_ok=True)
            if not filename.endswith('.png'):
                filename += '.png'
            final_path = os.path.join(final_out_dir, filename)
            shutil.move(os.path.join(temp_dir, png_temp), final_path)

            if save_tex:
                if not tex_filename.endswith('.tex'):
                    tex_filename += '.tex'
                shutil.copy(tex_path, os.path.join(final_out_dir, tex_filename))

            route_name = f"/output_{hash(final_out_dir)}"
            app.add_static_files(route_name, final_out_dir)
            img_url = f"{route_name}/{filename}?t={asyncio.get_event_loop().time()}"
            return True, logs, img_url, final_path
        else:
            logs.append("Error convirtiendo PDF a PNG.")
            return False, logs, None, None

    except Exception as e:
        logs.append(str(e))
        return False, logs, None, None
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


def create_folder_picker(target_input: ui.input):
    """Opens a dialog to browse the server filesystem and select a folder."""
    result = {'path': str(Path.home())}

    async def refresh_listing(path_str: str):
        result['path'] = path_str
        current_label.text = path_str
        listing_col.clear()
        p = Path(path_str)
        with listing_col:
            # Parent dir button
            if p.parent != p:
                ui.button(f'📁 ..  (up)', on_click=lambda: asyncio.ensure_future(refresh_listing(str(p.parent)))) \
                    .props('flat dense align=left').classes('w-full text-left font-mono text-sm')
            try:
                entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for entry in entries:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        name = entry.name
                        entry_path = str(entry)
                        ui.button(f'📁  {name}', on_click=lambda ep=entry_path: asyncio.ensure_future(refresh_listing(ep))) \
                            .props('flat dense align=left').classes('w-full text-left font-mono text-sm')
            except PermissionError:
                ui.label('Permission denied').classes('text-red-500 text-sm')

    def confirm_selection():
        target_input.value = result['path']
        dialog.close()

    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Select Output Folder').classes('text-lg font-bold mb-2')
        current_label = ui.label(result['path']).classes('text-xs text-gray-500 font-mono break-all mb-2')
        listing_col = ui.column().classes('w-full max-h-72 overflow-y-auto border rounded p-1 gap-0')
        asyncio.ensure_future(refresh_listing(result['path']))
        with ui.row().classes('w-full justify-end mt-3 gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            ui.button('Select This Folder', on_click=confirm_selection).props('color=primary')

    dialog.open()


@ui.page('/')
def editor_page():
    ui.colors(primary='#1e88e5', secondary='#26a69a', accent='#9c27b0', dark='#121212', positive='#43a047', negative='#e53935')

    # ── HEADER ────────────────────────────────────────────────────
    with ui.header().classes('items-center justify-between p-4 bg-primary text-white'):
        ui.label('ChemFig Editor').classes('text-2xl font-bold')

        with ui.row().classes('items-center gap-4'):
            dep_status = ui.label('')

            def verify_deps():
                missing = check_dependencies()
                if missing:
                    dep_status.text = f"Missing: {', '.join(missing)}"
                    dep_status.classes('text-red-200 font-bold', remove='text-green-200')
                else:
                    dep_status.text = "Dependencies: OK"
                    dep_status.classes('text-green-200 font-bold', remove='text-red-200')

            ui.button('Verify Dependencies', icon='check_circle', on_click=verify_deps).props('flat color=white')

            def download_tex():
                content = state['header'] + code_editor.value + "\n" + state['footer']
                ui.download(content.encode('utf-8'), f"{filename_input.value.replace('.png', '') or 'structure'}.tex")

            ui.button('Download .tex', icon='download', on_click=download_tex).props('flat color=white')

    # ── MAIN CONTENT ──────────────────────────────────────────────
    with ui.row().classes('w-full h-full p-4 gap-4 no-wrap'):

        # ── LEFT PANEL ────────────────────────────────────────────
        with ui.column().classes('w-1/2 h-full gap-0'):

            # LaTeX header editor
            with ui.expansion('Edit LaTeX Header', icon='settings').classes('w-full bg-gray-100 rounded mb-3'):
                header_editor = ui.textarea().classes('w-full').props('rows=8 font=monospace')
                header_editor.value = state['header']

                def update_header():
                    state['header'] = header_editor.value
                    ui.notify("Header updated")
                ui.button('Save Header', on_click=update_header).classes('mt-2')

            # ── SAVE OPTIONS (collapsible) ─────────────────────────
            with ui.expansion('Save Options', icon='save').classes('w-full bg-gray-100 rounded mb-3'):
                # Output directory row with Browse button
                with ui.row().classes('w-full items-center gap-2 mb-3'):
                    output_dir_input = ui.input('Output folder', value='assets/structures').classes('flex-grow')
                    ui.button(icon='folder_open', on_click=lambda: create_folder_picker(output_dir_input)) \
                        .props('flat dense color=primary').tooltip('Browse folder')

                # Image filename
                filename_input = ui.input('Image filename (e.g. preview.png)', value='preview.png').classes('w-full mb-3')

                ui.separator()

                # .tex save toggle + filename
                with ui.row().classes('w-full items-center gap-2 mt-2'):
                    save_tex_cb = ui.checkbox('Save .tex source')
                    tex_filename_input = ui.input('.tex filename', value='structure.tex').classes('flex-grow')
                    def toggle_tex_input():
                        tex_filename_input.set_enabled(save_tex_cb.value)
                    save_tex_cb.on('update:model-value', lambda: toggle_tex_input())
                    tex_filename_input.set_enabled(False)  # disabled until checkbox is ticked

            # ── CODE EDITOR ───────────────────────────────────────
            code_editor = ui.textarea(r'ChemFig Code (\schemestart … \schemestop)') \
                .classes('w-full flex-grow text-lg') \
                .style('font-family: "Source Code Pro", monospace; min-height: 280px')
            code_editor.value = r"""\schemestart
    \chemfig{*6(=-=(-(=[2]O)-[:-30]OH)-=(-Cl)-)}
\schemestop"""

            # ── GENERATE BUTTON ───────────────────────────────────
            current_img_path = {"path": None}

            async def trigger_compile():
                body = code_editor.value
                fname = filename_input.value or "preview.png"
                out_dir = output_dir_input.value or "assets/structures"
                tex_fname = tex_filename_input.value or "structure.tex"
                save_tex = save_tex_cb.value

                ui.notify('Compiling...', type='info')
                log_output.value = "Compiling...\n"

                success, logs, url, final_path = await compile_latex(body, fname, out_dir, save_tex, tex_fname)

                full_log = "\n".join(logs)
                log_output.value = full_log[-2000:]

                if success and url:
                    preview_img.set_source(url)
                    current_img_path["path"] = final_path
                    download_btn.set_visibility(True)
                    ui.notify('Success!', type='positive')
                else:
                    download_btn.set_visibility(False)
                    ui.notify('Error in compilation. Check the log.', type='negative')

            ui.button('Generate', icon='play_arrow', color='primary', on_click=trigger_compile) \
                .classes('w-full mb-2').props('size=lg')

        # ── RIGHT PANEL ───────────────────────────────────────────
        with ui.column().classes('w-1/2 h-full'):

            # Preview header row: label + auto-preview toggle
            with ui.row().classes('w-full items-center justify-between mb-2'):
                ui.label('Preview').classes('text-xl font-bold')
                auto_preview_cb = ui.checkbox('Auto-Preview')

            with ui.card().tight().classes('w-full h-64 items-center justify-center bg-gray-50'):
                preview_img = ui.image('').props('fit=scale-down')

            # Download image button (hidden until compile succeeds)
            download_btn = ui.button('Download Image', icon='download').classes('mt-2')
            download_btn.set_visibility(False)

            def do_download():
                if current_img_path["path"] and os.path.exists(current_img_path["path"]):
                    ui.download(current_img_path["path"])

            download_btn.on('click', do_download)

            ui.label('Log Output').classes('text-xl font-bold mt-4 mb-2')
            log_output = ui.textarea().classes('w-full h-20 bg-gray-50 text-red-500 p-2 rounded') \
                .props('readonly font=monospace')

    # ── AUTO-PREVIEW TIMER ────────────────────────────────────────
    async def check_auto_preview():
        if auto_preview_cb.value:
            current_code = code_editor.value
            if current_code != state['last_code']:
                state['last_code'] = current_code
                await trigger_compile()

    ui.timer(2.0, check_auto_preview)
    verify_deps()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='ChemFig Editor')
