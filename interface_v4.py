import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import platform
from airSpace import *
from navSegment import get_origin_number, get_destination_number, get_distance
from kml_generator import generate_airspace_kml, generate_path_kml, generate_neighbors_kml, save_kml_to_file
from music_generator import (MusicPlayer)
import music_generator
from PIL import Image, ImageTk, ImageFilter  # Añadir ImageFilter para el efecto de desenfoque
from path import find_shortest_path_astar, find_multiple_paths_astar  # Importar el algoritmo A*

# Variables globales
espacio_aereo = None
ultimo_archivo_nav = "Cat_nav.txt"
ultimo_archivo_seg = "Cat_seg.txt"
ultimo_archivo_aer = "Cat_aer.txt"
reproductor_musica = None  # Variable global para controlar el reproductor de música

# Temas de la aplicación
LIGHT_THEME = {
    "bg": "#f0f2f5",
    "fg": "#333333",
    "button_bg": "#4a6fa5",  # Azul más elegante
    "button_fg": "white",
    "button_active_bg": "#3a5a80",  # Color cuando se presiona
    "button_hover_bg": "#5a7fb5",   # Color al pasar el mouse
    "entry_bg": "white",
    "entry_fg": "#333333",
    "highlight_bg": "#e3f2fd",
    "frame_bg": "#f0f2f5",
    "text_bg": "white",
    "text_fg": "#333333",
    "plot_bg": "#f5f5f5",
    "plot_fg": "#333333",
    "grid_color": "#cccccc",
    "labelframe_bg": "#f0f2f5",  # Igual al fondo
    "labelframe_fg": "#333333",
    "status_bg": "#dcdcdc",
    "status_fg": "#333333",
    "font_family": "Segoe UI" if platform.system() == "Windows" else "Helvetica Neue",
    "font_size_normal": 10,
    "font_size_title": 12,
    "font_size_header": 22,
    "button_padx": 12,
    "button_pady": 6,
    "relief": tk.RAISED,
    "borderwidth": 1
}

DARK_THEME = {
    "bg": "#1a1a2e",
    "fg": "#e0e0e0",
    "button_bg": "#3a506b",  # Azul medio elegante
    "button_fg": "#ffffff",
    "button_active_bg": "#2a405b",  # Color cuando se presiona
    "button_hover_bg": "#4a607b",   # Color al pasar el mouse
    "entry_bg": "#16213e",
    "entry_fg": "#e0e0e0",
    "highlight_bg": "#1e3a5f",
    "frame_bg": "#1a1a2e",
    "text_bg": "#16213e",
    "text_fg": "#e0e0e0",
    "plot_bg": "#16213e",
    "plot_fg": "#e0e0e0",
    "grid_color": "#333333",
    "labelframe_bg": "#1a1a2e",  # Igual al fondo
    "labelframe_fg": "#e0e0e0",
    "status_bg": "#16213e",
    "status_fg": "#e0e0e0",
    "font_family": "Segoe UI" if platform.system() == "Windows" else "Helvetica Neue",
    "font_size_normal": 10,
    "font_size_title": 12,
    "font_size_header": 22,
    "button_padx": 12,
    "button_pady": 6,
    "relief": tk.RAISED,
    "borderwidth": 1
}

# Funciones de utilidad para obtener puntos y segmentos
def get_navpoint_by_name(airspace, name):
    """Obtiene un objeto NavPoint por su nombre."""
    for point in airspace.navpoints.values():
        if point.name == name:
            return point
    return None

def get_navpoint_by_number(airspace, number):
    """Obtiene un objeto NavPoint por su número."""
    return airspace.navpoints.get(number)

def get_navairport_by_name(airspace, name):
    """Obtiene un objeto NavAirport por su nombre."""
    return airspace.navairports.get(name)

def get_navsegment_by_number(airspace, number):
    """Obtiene un objeto NavSegment por su número."""
    return airspace.navsegments.get(number)

def explorar_archivo(variable_texto):
    nombre_archivo = filedialog.askopenfilename(
        initialdir=".",
        title="Seleccione un archivo",
        filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")) )

    if nombre_archivo:
        variable_texto.set(nombre_archivo)

def explorar_archivo_nav(app, archivo_nav):
    explorar_archivo(archivo_nav)

def explorar_archivo_seg(app, archivo_seg):
    explorar_archivo(archivo_seg)

def explorar_archivo_aer(app, archivo_aer):
    explorar_archivo(archivo_aer)

def cargar_datos_wrapper(app, archivo_nav, archivo_seg, archivo_aer, ventana):
    nav = archivo_nav.get()
    seg = archivo_seg.get()
    aer = archivo_aer.get()
    cargar_datos(app, nav, seg, aer, ventana)

def cargar_datos(app, archivo_nav, archivo_seg, archivo_aer, ventana):
    global espacio_aereo
    global ultimo_archivo_nav, ultimo_archivo_seg, ultimo_archivo_aer

    try:
        espacio_aereo = AirSpace()

        exito = load_from_files(espacio_aereo, archivo_nav, archivo_seg, archivo_aer)

        if exito:
            # Actualizar los últimos archivos cargados
            ultimo_archivo_nav = archivo_nav
            ultimo_archivo_seg = archivo_seg
            ultimo_archivo_aer = archivo_aer
            
            messagebox.showinfo("Éxito", f"Datos cargados correctamente.\n\nPuntos de navegación: {len(espacio_aereo.navpoints)}\nSegmentos: {len(espacio_aereo.navsegments)}\nAeropuertos: {len(espacio_aereo.navairports)}", parent=ventana)
            ventana.destroy()

            app.status.config(text=f"Datos cargados: {len(espacio_aereo.navpoints)} puntos, {len(espacio_aereo.navsegments)} segmentos, {len(espacio_aereo.navairports)} aeropuertos")

            # Habilitar el botón de exportación cuando se cargan los datos
            if hasattr(app, 'export_btn'):
                app.export_btn.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Error", "No se pudieron cargar los datos correctamente.", parent=ventana)
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar datos: {str(e)}", parent=ventana)

def limpiar_contenido(app):
    content_window = tk.Toplevel(app)
    content_window.title("Contenido de Espacio Aéreo")
    content_window.geometry("700x500")
    return content_window

def cargar_espacio_aereo(app):
    global espacio_aereo

    load_window = tk.Toplevel(app)
    load_window.title("Cargar Datos de Espacio Aéreo")
    load_window.geometry("450x250")
    load_window.configure(bg=app.tema["bg"])  # Aplicar el color de fondo del tema actual

    file_frame = tk.Frame(load_window, bg=app.tema["bg"])
    file_frame.pack(fill=tk.X, pady=10, padx=10)

    nav_label = tk.Label(file_frame, text="Archivo de Puntos de Navegación:", 
                         bg=app.tema["bg"], fg=app.tema["fg"],
                         font=(app.tema["font_family"], app.tema["font_size_normal"]))
    nav_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

    nav_file = tk.StringVar(value=ultimo_archivo_nav)
    nav_entry = tk.Entry(file_frame, textvariable=nav_file, width=30,
                         bg=app.tema["entry_bg"], fg=app.tema["entry_fg"],
                         insertbackground=app.tema["entry_fg"])
    nav_entry.grid(row=0, column=1, padx=5, pady=5)

    nav_browse = tk.Button(file_frame, text="...",
                        command=lambda: explorar_archivo_nav(app, nav_file),
                        bg=app.tema["button_bg"], fg=app.tema["button_fg"],
                        activebackground=app.tema["button_active_bg"])
    nav_browse.grid(row=0, column=2, padx=5, pady=5)

    seg_label = tk.Label(file_frame, text="Archivo de Segmentos:", 
                       bg=app.tema["bg"], fg=app.tema["fg"],
                       font=(app.tema["font_family"], app.tema["font_size_normal"]))
    seg_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

    seg_file = tk.StringVar(value=ultimo_archivo_seg)
    seg_entry = tk.Entry(file_frame, textvariable=seg_file, width=30,
                       bg=app.tema["entry_bg"], fg=app.tema["entry_fg"],
                       insertbackground=app.tema["entry_fg"])
    seg_entry.grid(row=1, column=1, padx=5, pady=5)

    seg_browse = tk.Button(file_frame, text="...",
                        command=lambda: explorar_archivo_seg(app, seg_file),
                        bg=app.tema["button_bg"], fg=app.tema["button_fg"],
                        activebackground=app.tema["button_active_bg"])
    seg_browse.grid(row=1, column=2, padx=5, pady=5)

    air_label = tk.Label(file_frame, text="Archivo de Aeropuertos:", 
                       bg=app.tema["bg"], fg=app.tema["fg"],
                       font=(app.tema["font_family"], app.tema["font_size_normal"]))
    air_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

    air_file = tk.StringVar(value=ultimo_archivo_aer)
    air_entry = tk.Entry(file_frame, textvariable=air_file, width=30,
                       bg=app.tema["entry_bg"], fg=app.tema["entry_fg"],
                       insertbackground=app.tema["entry_fg"])
    air_entry.grid(row=2, column=1, padx=5, pady=5)


    air_browse = tk.Button(file_frame, text="...",
                        command=lambda: explorar_archivo_aer(app, air_file),
                        bg=app.tema["button_bg"], fg=app.tema["button_fg"],
                        activebackground=app.tema["button_active_bg"])
    air_browse.grid(row=2, column=2, padx=5, pady=5)


    load_button = tk.Button(load_window, text="Cargar Datos",
                         command=lambda: cargar_datos_wrapper(app, nav_file, seg_file, air_file, load_window),
                         bg=app.tema["button_bg"], fg=app.tema["button_fg"],
                         activebackground=app.tema["button_active_bg"],
                         font=(app.tema["font_family"], app.tema["font_size_normal"]),
                         padx=app.tema["button_padx"], pady=app.tema["button_pady"])
    load_button.pack(pady=10)

def mostrar_espacio_aereo(app, punto_destacado=None, vecinos=None, ruta=None):
    global espacio_aereo

    if not espacio_aereo or not espacio_aereo.navpoints:
        messagebox.showwarning("Advertencia", "No hay datos de espacio aéreo cargados. Por favor cargue los datos primero.")
        return

    map_window = tk.Toplevel(app)
    map_window.title("Mapa de Espacio Aéreo")
    map_window.geometry("1200x900")
    
    # Aplicar estilo consistente a la ventana emergente
    map_window.configure(bg=app.tema["bg"])

    # Variables para controlar la visibilidad de elementos
    show_nodes = tk.BooleanVar(value=True)
    show_segments = tk.BooleanVar(value=True)
    show_distances = tk.BooleanVar(value=True)

    # Crear el panel de control para los botones de visibilidad (ahora al principio)
    control_frame = tk.Frame(map_window, bg=app.tema["bg"])
    control_frame.pack(side=tk.TOP, fill=tk.X)

    visibility_label = tk.Label(control_frame, text="Controles de visibilidad:", 
                              font=(app.tema["font_family"], app.tema["font_size_normal"]),
                              bg=app.tema["bg"], fg=app.tema["fg"])
    visibility_label.pack(side=tk.LEFT, padx=5)

    # Botón para mostrar/ocultar nodos
    nodes_check = tk.Checkbutton(control_frame, text="Mostrar Nodos", variable=show_nodes,
                                font=(app.tema["font_family"], app.tema["font_size_normal"]),
                                bg=app.tema["bg"], fg=app.tema["fg"],
                                selectcolor=app.tema["bg"] if platform.system() == "Darwin" else None)
    nodes_check.pack(side=tk.LEFT, padx=10)

    # Botón para mostrar/ocultar segmentos
    segments_check = tk.Checkbutton(control_frame, text="Mostrar Segmentos", variable=show_segments,
                                   font=(app.tema["font_family"], app.tema["font_size_normal"]),
                                   bg=app.tema["bg"], fg=app.tema["fg"],
                                   selectcolor=app.tema["bg"] if platform.system() == "Darwin" else None)
    segments_check.pack(side=tk.LEFT, padx=10)

    # Botón para mostrar/ocultar distancias
    distances_check = tk.Checkbutton(control_frame, text="Mostrar Distancias", variable=show_distances,
                                    font=(app.tema["font_family"], app.tema["font_size_normal"]),
                                    bg=app.tema["bg"], fg=app.tema["fg"],
                                    selectcolor=app.tema["bg"] if platform.system() == "Darwin" else None)
    distances_check.pack(side=tk.LEFT, padx=10)

    fig = Figure(figsize=(15, 12), dpi=100)
    ax = fig.add_subplot(111)

    is_neighbor_view = bool(punto_destacado and vecinos)

    lon_values = []
    lat_values = []

    point_cache = {}

    for num, point in espacio_aereo.navpoints.items():
        lon_values.append(point.longitude)
        lat_values.append(point.latitude)
        point_cache[point.number] = point


    margin = 0.1
    lon_min = min(lon_values) - margin
    lon_max = max(lon_values) + margin
    lat_min = min(lat_values) - margin
    lat_max = max(lat_values) + margin


    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_autoscale_on(False)  # Disable autoscaling
    ax.set_clip_on(True)

    segment_color = 'cyan'
    point_color = 'black'
    highlight_color = 'red'
    neighbor_color = highlight_color
    path_color = '#00CCCC'

    fig.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.05)

    canvas = FigureCanvasTkAgg(fig, master=map_window)  # A tk.DrawingArea.

    # Create a proper layout for the canvas and toolbar
    canvas_frame = tk.Frame(map_window)
    canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
    toolbar.update()

    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Función para redibujar el mapa según las opciones de visibilidad
    def redraw_map():
        ax.clear()
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
        ax.set_autoscale_on(False)
        ax.set_clip_on(True)
        ax.set_clip_box(ax.bbox)

        # Dibujar segmentos si están habilitados
        if show_segments.get():
            for segment in espacio_aereo.navsegments:
                point1 = point_cache.get(segment.origin_number)
                point2 = point_cache.get(segment.destination_number)

                if point1 and point2:
                    draw_this_segment = False
                    current_line_color = segment_color
                    current_line_width = 1.0

                    if is_neighbor_view:
                        neighbor_numbers = [n[0].number for n in vecinos]
                        if (point1.number == punto_destacado.number and point2.number in neighbor_numbers) or \
                           (point2.number == punto_destacado.number and point1.number in neighbor_numbers):
                            current_line_color = segment_color
                            current_line_width = 1.0
                            draw_this_segment = True
                    else:
                        if ruta:
                            draw_this_segment = False
                            for i in range(len(ruta) - 1):
                                if ((ruta[i].number == point1.number and ruta[i+1].number == point2.number) or
                                    (ruta[i].number == point2.number and ruta[i+1].number == point1.number)):
                                    draw_this_segment = True
                                    current_line_color = '#00CCCC'
                                    current_line_width = 1.5

                                    if ruta[i].number == point1.number and ruta[i+1].number == point2.number:
                                        start_point = (point1.longitude, point1.latitude)
                                        end_point = (point2.longitude, point2.latitude)
                                    else:
                                        start_point = (point2.longitude, point2.latitude)
                                        end_point = (point1.longitude, point1.latitude)
                                    break
                        else:
                            draw_this_segment = True
                            current_line_color = segment_color
                            current_line_width = 1.0

                    if draw_this_segment:
                        start_point = (point1.longitude, point1.latitude)
                        end_point = (point2.longitude, point2.latitude)

                        # Usar ax.plot en lugar de ax.annotate para mejorar el comportamiento al hacer zoom
                        x_coords = [start_point[0], end_point[0]]
                        y_coords = [start_point[1], end_point[1]]
                        line = ax.plot(x_coords, y_coords, color=current_line_color, 
                                      linewidth=current_line_width, 
                                      clip_on=True, zorder=5)[0]
                        
                        # Añadir una flecha de dirección
                        mid_point = 0.5  # Punto medio del segmento
                        arrow_props = dict(arrowstyle='-|>', color=current_line_color, 
                                         shrinkA=0, shrinkB=0, 
                                         lw=current_line_width*1.5, 
                                         mutation_scale=12,  # Aumentar el tamaño de la punta de flecha
                                         clip_on=True)
                        ax.annotate('', 
                                  xy=(x_coords[0] + mid_point*(x_coords[1]-x_coords[0]), 
                                     y_coords[0] + mid_point*(y_coords[1]-y_coords[0])),
                                  xytext=(x_coords[0] + (mid_point-0.02)*(x_coords[1]-x_coords[0]), 
                                         y_coords[0] + (mid_point-0.02)*(y_coords[1]-y_coords[0])),
                                  arrowprops=arrow_props,
                                  clip_on=True)

                        # Mostrar distancias si están habilitadas
                        if show_distances.get():
                            mid_x = (point1.longitude + point2.longitude) / 2
                            mid_y = (point1.latitude + point2.latitude) / 2
                            ax.text(mid_x, mid_y, f"{segment.distance:.1f}",
                                    fontsize=6, ha='center', va='center',
                                    bbox=dict(facecolor='white', alpha=0.5, pad=0.5), zorder=2, clip_on=True)

        # Dibujar nodos si están habilitados
        if show_nodes.get():
            for num, point in espacio_aereo.navpoints.items():
                this_color = point_color
                this_size = 5
                this_alpha = 1.0
                this_zorder = 10

                if ruta and any(p.number == point.number for p in ruta):
                    this_color = '#00CCCC'
                    this_size = 10
                    this_zorder = 20
                elif ruta:
                    this_alpha = 0.5
                    this_size = 4
                elif is_neighbor_view:
                    neighbor_numbers = [n[0].number for n in vecinos]
                    if point.number == punto_destacado.number:
                        this_color = highlight_color
                        this_size = 30
                    elif point.number in neighbor_numbers:
                        this_color = neighbor_color
                        this_size = 20
                    else:
                        this_color = 'gray'
                        this_size = 5

                ax.scatter(point.longitude, point.latitude, color=this_color, s=this_size, alpha=this_alpha, zorder=this_zorder, clip_on=True)

                ax.text(point.longitude + 0.01, point.latitude + 0.01, point.name,
                        fontsize=6, ha='left', va='bottom', zorder=6, clip_on=True)

        if not is_neighbor_view and not ruta:
            ax.grid(True, linestyle=':', alpha=0.7, color='red')

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor('black')
            spine.set_linewidth(0.5)

        if ruta:
            total_cost = 0
            for i in range(len(ruta) - 1):
                current_point = ruta[i]
                next_point = ruta[i+1]
                
                # Buscar el segmento entre los puntos y sumar su distancia
                for segment in espacio_aereo.navsegments:
                    if ((get_origin_number(segment) == current_point.number and get_destination_number(segment) == next_point.number) or
                        (get_origin_number(segment) == next_point.number and get_destination_number(segment) == current_point.number)):
                        total_cost += get_distance(segment)
                        break
            
            ax.set_title(f"Gráfico con camino. Coste = {total_cost:.8f}", pad=20, y=1.02)
        elif is_neighbor_view:
            ax.set_title(f"Grafico con los vecinos del nodo {punto_destacado.name}", fontsize=14, pad=20, y=1.02)
        else:
            ax.set_title("Gráfico con nodos y segmentos", fontsize=14, pad=20, y=1.02)

        canvas.draw()

    # Ahora conectamos los comandos a los checkbuttons
    nodes_check.config(command=redraw_map)
    segments_check.config(command=redraw_map)
    distances_check.config(command=redraw_map)

    # Dibujo inicial del mapa
    redraw_map()

    instructions_text = "Utilice la barra de herramientas para navegar por el mapa y los controles de visibilidad para personalizar la vista."
    instructions_label = tk.Label(map_window, text=instructions_text, font=("Arial", 10), bg=app.tema["bg"], fg=app.tema["fg"])
    instructions_label.pack(pady=5)

    # Añadir botón de exportación a Google Earth
    export_frame = tk.Frame(map_window, bg=app.tema["bg"])
    export_frame.pack(fill=tk.X, padx=10, pady=5)

    export_btn = tk.Button(export_frame, text="Exportar a Google Earth",
                          command=lambda: exportar_a_google_earth(app, ruta, punto_destacado, vecinos),
                          bg=app.tema["button_bg"], fg=app.tema["button_fg"])
    export_btn.pack(side=tk.LEFT, padx=5, pady=5)

    # Añadir botón de música en la esquina inferior izquierda
    music_btn = tk.Button(export_frame, text="Reproducir Música",
                         command=lambda: toggle_musica(app),
                         bg="#1E88E5",  # Azul más suave
                         fg="white",
                         font=("Arial", 10),
                         padx=10,
                         pady=5)
    music_btn.pack(side=tk.LEFT, padx=20, pady=5)

    status_message = "Mostrando mapa de espacio aéreo"
    if punto_destacado:
        status_message += f" - Destacando punto: {punto_destacado.name}"
    elif vecinos:
        status_message += f" - Mostrando {len(vecinos)} vecinos"
    elif ruta:
        status_message += f" - Mostrando ruta con {len(ruta)} puntos"

    app.status.config(text=status_message)

    return canvas, ax

def mostrar_vecinos(app):
    global espacio_aereo

    if not espacio_aereo or not espacio_aereo.navpoints:
        messagebox.showwarning("Advertencia", "No hay datos de espacio aéreo cargados. Por favor cargue los datos primero.")
        return

    neighbors_window = tk.Toplevel(app)
    neighbors_window.title("Encontrar Vecinos")
    neighbors_window.geometry("500x400")

    # Aplicar el tema actual a la ventana
    tema = app.tema
    neighbors_window.configure(bg=tema["bg"])

    input_frame = tk.Frame(neighbors_window, bg=tema["bg"])
    input_frame.pack(fill=tk.X, pady=10, padx=10)

    point_label = tk.Label(input_frame, text="Punto de Navegación:", bg=tema["bg"], fg=tema["fg"])
    point_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

    nav_point = tk.StringVar()
    point_entry = tk.Entry(input_frame, textvariable=nav_point, width=20, bg=tema["entry_bg"], fg=tema["entry_fg"])
    point_entry.grid(row=0, column=1, padx=5, pady=5)

    results_text = tk.Text(neighbors_window, width=50, height=15, bg=tema["text_bg"], fg=tema["text_fg"])
    results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(results_text)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    results_text.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=results_text.yview)

    button_frame = tk.Frame(neighbors_window, bg=tema["bg"])
    button_frame.pack(fill=tk.X, pady=5)

    find_button = tk.Button(button_frame, text="Encontrar Vecinos",
                         command=lambda: encontrar_y_mostrar_vecinos(app, results_text, nav_point),
                         bg=tema["button_bg"], fg=tema["button_fg"])
    find_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Botón para exportar vecinos a Google Earth
    export_button = tk.Button(button_frame, text="Exportar a Google Earth",
                             command=lambda: exportar_vecinos_a_google_earth(app, nav_point),
                             state=tk.DISABLED if not espacio_aereo else tk.NORMAL,
                             bg=tema["button_bg"], fg=tema["button_fg"])
    export_button.pack(side=tk.LEFT, padx=5, pady=5)

def encontrar_y_mostrar_vecinos(app, results_text, nav_point):
    global espacio_aereo

    results_text.delete(1.0, tk.END)

    nav_name = nav_point.get().strip()

    if not nav_name:
        messagebox.showwarning("Advertencia", "Por favor ingrese un nombre de punto de navegación.")
        return

    found_point = get_navpoint_by_name(espacio_aereo, nav_name)

    if not found_point:
        results_text.insert(tk.END, f"Punto de navegación '{nav_name}' no encontrado.")
        return

    vecinos = []
    for segment in espacio_aereo.navsegments:
        if get_origin_number(segment) == found_point.number:
            destination_number = get_destination_number(segment)
            if destination_number in espacio_aereo.navpoints:
                vecino = espacio_aereo.navpoints[destination_number]
                distancia = get_distance(segment)
                vecinos.append((vecino, distancia))

    vecinos.sort(key=lambda x: x[0].name)

    result_text = f"Vecinos de {found_point.name} (Número: {found_point.number}):\n"
    result_text += f"Ubicación: ({found_point.latitude}, {found_point.longitude})\n\n"

    if vecinos:
        for neighbor_info in vecinos:
            neighbor = neighbor_info[0]
            distance = neighbor_info[1]
            result_text += f"{neighbor.name} (Número: {neighbor.number}) - Distancia: {distance:.2f}\n"
    else:
        result_text += "No se encontraron vecinos."

    results_text.insert(tk.END, result_text)

    mostrar_espacio_aereo(app, punto_destacado=found_point, vecinos=vecinos)

    app.status.config(text=f"Encontrados {len(vecinos)} vecinos para {found_point.name}")

    # Guardar los vecinos encontrados para posible exportación
    app.last_neighbors_data = (found_point, vecinos)

def exportar_vecinos_a_google_earth(app, nav_point):
    global espacio_aereo
    
    nav_name = nav_point.get().strip()
    
    if not nav_name:
        messagebox.showwarning("Advertencia", "Por favor ingrese un nombre de punto de navegación.")
        return
        
    # Intentar obtener el punto de navegación
    found_point = get_navpoint_by_name(espacio_aereo, nav_name)
    
    if not found_point:
        messagebox.showwarning("Advertencia", f"Punto de navegación '{nav_name}' no encontrado.")
        return
        
    # Buscar vecinos del punto
    vecinos = []
    for segment in espacio_aereo.navsegments:
        if get_origin_number(segment) == found_point.number:
            destination_number = get_destination_number(segment)
            if destination_number in espacio_aereo.navpoints:
                vecino = espacio_aereo.navpoints[destination_number]
                distancia = get_distance(segment)
                vecinos.append((vecino, distancia))
                
    if not vecinos:
        messagebox.showwarning("Advertencia", f"No se encontraron vecinos para '{nav_name}'.")
        return
    
    # Verificar si tenemos vecinos antes de intentar exportar
    if not vecinos:
        messagebox.showwarning("Advertencia", f"No se encontraron vecinos para '{nav_name}'.")
        return
    
    try:
        # Crear contenido KML directamente aquí
        kml_content = generate_neighbors_kml(found_point, vecinos, espacio_aereo)
        
        # Solicitar ubicación para guardar
        filename = filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=[("Archivos KML", "*.kml"), ("Todos los archivos", "*.*")],
            title=f"Guardar vecinos de {nav_name} como KML"
        )
        
        if not filename:
            return  # Usuario canceló el diálogo
            
        # Asegurarse de que el archivo tenga extensión .kml
        if not filename.lower().endswith('.kml'):
            filename += '.kml'
            
        # Guardar el archivo
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            messagebox.showinfo("Éxito", f"Vecinos de {nav_name} exportados a {filename}")
            
            # Preguntar si quiere abrir en Google Earth
            if messagebox.askyesno("Abrir en Google Earth", "¿Desea abrir el archivo en Google Earth?"):
                try:
                    os.startfile(filename)
                except Exception as e:
                    messagebox.showwarning("Error", f"No se pudo abrir Google Earth automáticamente: {str(e)}\nPor favor, abra el archivo manualmente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al generar el KML: {str(e)}")

def encontrar_ruta(app):
    """Abre una ventana para encontrar una ruta entre dos puntos."""
    global espacio_aereo

    if not espacio_aereo:
        messagebox.showerror("Error", "No hay datos cargados.")
        return

    ventana = tk.Toplevel(app)
    ventana.title("Encontrar Ruta")
    ventana.geometry("600x500")
    ventana.configure(bg=app.tema["bg"])

    # Frame para entrada de datos
    frame_entrada = tk.Frame(ventana, bg=app.tema["bg"])
    frame_entrada.pack(fill="x", padx=20, pady=10)

    # Etiquetas y entradas para origen y destino
    tk.Label(frame_entrada, text="Origen:", bg=app.tema["bg"], fg=app.tema["fg"]).grid(row=0, column=0, padx=5, pady=5)
    origin_point = tk.StringVar()
    entrada_origen = tk.Entry(frame_entrada, textvariable=origin_point, bg=app.tema["entry_bg"], fg=app.tema["entry_fg"])
    entrada_origen.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_entrada, text="Destino:", bg=app.tema["bg"], fg=app.tema["fg"]).grid(row=1, column=0, padx=5, pady=5)
    dest_point = tk.StringVar()
    entrada_destino = tk.Entry(frame_entrada, textvariable=dest_point, bg=app.tema["entry_bg"], fg=app.tema["entry_fg"])
    entrada_destino.grid(row=1, column=1, padx=5, pady=5)

    # Frame para botones
    frame_botones = tk.Frame(ventana, bg=app.tema["bg"])
    frame_botones.pack(fill="x", padx=20, pady=5)

    # Botón para encontrar ruta más corta
    tk.Button(
        frame_botones,
        text="Encontrar Ruta Más Corta",
        command=lambda: encontrar_y_mostrar_ruta(app, path_text, origin_point, dest_point),
        bg=app.tema["button_bg"],
        fg=app.tema["button_fg"],
        font=("Segoe UI", 10),
        padx=12,
        pady=6
    ).pack(side=tk.LEFT, padx=5)

    # Botón para exportar a Google Earth
    tk.Button(
        frame_botones,
        text="Exportar a Google Earth",
        command=lambda: exportar_ruta_a_google_earth_helper(app, app.last_path_data[0]) if hasattr(app, 'last_path_data') and app.last_path_data else messagebox.showinfo("Información", "Primero debes calcular una ruta para poder exportarla."),
        bg=app.tema["button_bg"],
        fg=app.tema["button_fg"],
        font=("Segoe UI", 10),
        padx=12,
        pady=6
    ).pack(side=tk.LEFT, padx=5)

    # Botón para comparar rutas
    tk.Button(
        frame_botones,
        text="Comparar Rutas Alternativas",
        command=lambda: comparar_rutas(app, origin_point, dest_point),
        bg=app.tema["button_bg"],
        fg=app.tema["button_fg"],
        font=("Segoe UI", 10),
        padx=12,
        pady=6
    ).pack(side=tk.LEFT, padx=5)

    # Área de texto para mostrar resultados
    path_text = tk.Text(ventana, height=15, bg=app.tema["text_bg"], fg=app.tema["text_fg"])
    path_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

def encontrar_y_mostrar_ruta(app, path_text, origin_point, dest_point):
    path_text.delete(1.0, tk.END)

    origin_name = origin_point.get().strip()
    dest_name = dest_point.get().strip()

    if not origin_name or not dest_name:
        messagebox.showwarning("Advertencia", "Por favor ingrese nombres para el origen y destino.")
        return

    # Verificar si el origen es un aeropuerto
    origin_is_airport = origin_name.startswith(("LE", "LF"))
    if origin_is_airport:
        origin_airport = get_navairport_by_name(espacio_aereo, origin_name)
        if not origin_airport:
            path_text.insert(tk.END, f"ERROR: No se encontró ningún aeropuerto con el código '{origin_name}'.\n")
            path_text.insert(tk.END, "Por favor verifique que el código del aeropuerto de origen sea correcto.\n")
            return
        origin = origin_name  # Usamos el código del aeropuerto directamente
    else:
        # Buscar como punto de navegación normal
        origin = get_navpoint_by_name(espacio_aereo, origin_name)
        if not origin:
            path_text.insert(tk.END, f"ERROR: No se encontró ningún punto con el nombre '{origin_name}'.\n")
            path_text.insert(tk.END, "Por favor verifique que el nombre del punto de origen sea correcto.\n")
            return

    # Verificar si el destino es un aeropuerto
    dest_is_airport = dest_name.startswith(("LE", "LF"))
    if dest_is_airport:
        dest_airport = get_navairport_by_name(espacio_aereo, dest_name)
        if not dest_airport:
            path_text.insert(tk.END, f"ERROR: No se encontró ningún aeropuerto con el código '{dest_name}'.\n")
            path_text.insert(tk.END, "Por favor verifique que el código del aeropuerto de destino sea correcto.\n")
            return
        dest = dest_name  # Usamos el código del aeropuerto directamente
    else:
        # Buscar como punto de navegación normal
        dest = get_navpoint_by_name(espacio_aereo, dest_name)
        if not dest:
            path_text.insert(tk.END, f"ERROR: No se encontró ningún punto con el nombre '{dest_name}'.\n")
            path_text.insert(tk.END, "Por favor verifique que el nombre del punto de destino sea correcto.\n")
            return

    # Si son puntos de navegación normales, verificar si tienen segmentos conectados
    if not origin_is_airport and not dest_is_airport:
        origin_has_segments = False
        dest_has_segments = False
        
        for segment in espacio_aereo.navsegments:
            if segment.origin_number == origin.number or segment.destination_number == origin.number:
                origin_has_segments = True
            if segment.origin_number == dest.number or segment.destination_number == dest.number:
                dest_has_segments = True
        
        if not origin_has_segments:
            path_text.insert(tk.END, f"ERROR: El punto '{origin.name}' no está conectado a ningún segmento.\n")
            path_text.insert(tk.END, "Este punto está aislado en el grafo de navegación y no puede ser utilizado para ruteo.\n")
            return
        
        if not dest_has_segments:
            path_text.insert(tk.END, f"ERROR: El punto '{dest.name}' no está conectado a ningún segmento.\n")
            path_text.insert(tk.END, "Este punto está aislado en el grafo de navegación y no puede ser utilizado para ruteo.\n")
            return

    # Mensaje personalizado según los tipos de origen y destino
    if origin_is_airport and dest_is_airport:
        path_text.insert(tk.END, f"Buscando ruta del aeropuerto {origin_name} al aeropuerto {dest_name} usando algoritmo A*...\n\n")
        
        # Mostrar información de los aeropuertos para depuración
        path_text.insert(tk.END, f"[Debug] Aeropuerto origen ({origin_name}):\n")
        if origin_airport.sids:
            path_text.insert(tk.END, f"  SIDs: {origin_airport.sids}\n")
        else:
            path_text.insert(tk.END, "  No tiene SIDs definidos\n")
        
        path_text.insert(tk.END, f"[Debug] Aeropuerto destino ({dest_name}):\n")
        if dest_airport.stars:
            path_text.insert(tk.END, f"  STARs: {dest_airport.stars}\n")
        else:
            path_text.insert(tk.END, "  No tiene STARs definidos\n")
        
        path_text.insert(tk.END, "\n")
    elif origin_is_airport:
        path_text.insert(tk.END, f"Buscando ruta del aeropuerto {origin_name} al punto {dest_name} usando algoritmo A*...\n\n")
    elif dest_is_airport:
        path_text.insert(tk.END, f"Buscando ruta del punto {origin_name} al aeropuerto {dest_name} usando algoritmo A*...\n\n")
    else:
        path_text.insert(tk.END, f"Buscando ruta de {origin_name} a {dest_name} usando algoritmo A*...\n\n")

    # Usar el algoritmo A* para encontrar la ruta (con depuración activada)
    path_points, total_distance = find_shortest_path_astar(espacio_aereo, origin, dest, debug=True)

    if not path_points:
        path_text.insert(tk.END, "No se encontró ninguna ruta entre estos puntos.\n")
        if origin_is_airport or dest_is_airport:
            path_text.insert(tk.END, "Esto puede deberse a que no existen SIDs o STARs que permitan conectar los aeropuertos,\n")
            path_text.insert(tk.END, "o a que se encuentran en componentes desconectados del grafo de navegación.\n")
        else:
            path_text.insert(tk.END, "Ambos puntos tienen segmentos conectados, pero no existe un camino que los una.\n")
            path_text.insert(tk.END, "Esto puede deberse a que se encuentran en componentes desconectados del grafo de navegación.\n")
        return

    path_text.insert(tk.END, f"Ruta encontrada: {len(path_points)} puntos\n")
    path_text.insert(tk.END, f"Distancia total: {total_distance:.2f} km\n\n")

    path_text.insert(tk.END, "Puntos de la ruta:\n")
    for i, point in enumerate(path_points):
        path_text.insert(tk.END, f"{i+1}. {point.name} (#{point.number})\n")

    # Mostrar la ruta en el mapa
    mostrar_espacio_aereo(app, ruta=path_points)

    # Guardar los datos de la ruta para exportación posterior
    app.last_path_data = (path_points, total_distance)

def comparar_rutas(app, origin_point=None, dest_point=None):
    """Abre una nueva ventana para comparar diferentes rutas entre dos puntos."""
    ventana_comparacion = tk.Toplevel(app)
    ventana_comparacion.title("Comparar Rutas")
    ventana_comparacion.geometry("800x600")
    ventana_comparacion.configure(bg=app.tema["bg"])

    # Frame principal
    frame_principal = tk.Frame(ventana_comparacion, bg=app.tema["bg"])
    frame_principal.pack(fill="both", expand=True, padx=20, pady=10)

    # Frame para entrada de datos
    frame_entrada = tk.Frame(frame_principal, bg=app.tema["bg"])
    frame_entrada.pack(fill="x", pady=10)

    # Etiquetas y entradas para origen y destino
    tk.Label(frame_entrada, text="Origen:", bg=app.tema["bg"], fg=app.tema["fg"]).pack(side=tk.LEFT, padx=5)
    origen = tk.StringVar(value=origin_point.get() if origin_point else "")
    entrada_origen = tk.Entry(frame_entrada, textvariable=origen, bg=app.tema["entry_bg"], fg=app.tema["entry_fg"])
    entrada_origen.pack(side=tk.LEFT, padx=5)

    tk.Label(frame_entrada, text="Destino:", bg=app.tema["bg"], fg=app.tema["fg"]).pack(side=tk.LEFT, padx=5)
    destino = tk.StringVar(value=dest_point.get() if dest_point else "")
    entrada_destino = tk.Entry(frame_entrada, textvariable=destino, bg=app.tema["entry_bg"], fg=app.tema["entry_fg"])
    entrada_destino.pack(side=tk.LEFT, padx=5)

    # Frame para resultados
    frame_resultados = tk.Frame(frame_principal, bg=app.tema["bg"])
    frame_resultados.pack(fill="both", expand=True, pady=10)

    # Área de texto para mostrar resultados
    resultados_text = tk.Text(frame_resultados, height=10, bg=app.tema["text_bg"], fg=app.tema["text_fg"])
    resultados_text.pack(fill="both", expand=True)

    # Frame para botones
    frame_botones = tk.Frame(frame_principal, bg=app.tema["bg"])
    frame_botones.pack(fill="x", pady=10)

    # Frame para botones de acción (búsqueda y exportación)
    frame_acciones = tk.Frame(frame_entrada, bg=app.tema["bg"])
    frame_acciones.pack(side=tk.LEFT, padx=5)

    # Botón de búsqueda
    tk.Button(
        frame_acciones,
        text="Buscar Rutas",
        command=lambda: buscar_rutas(app, origen, destino, resultados_text, frame_botones),
        bg=app.tema["button_bg"],
        fg=app.tema["button_fg"],
        font=("Segoe UI", 10)
    ).pack(side=tk.LEFT, padx=5)

def buscar_rutas(app, origen, destino, path_text, frame_botones):
    """Busca y muestra múltiples rutas entre dos puntos."""
    global espacio_aereo

    try:
        # Limpiar el texto anterior
        path_text.delete(1.0, tk.END)

        # Limpiar botones anteriores
        for widget in frame_botones.winfo_children():
            widget.destroy()

        # Obtener nombres de origen y destino
        origin_name = origen.get().strip()
        dest_name = destino.get().strip()

        if not origin_name or not dest_name:
            messagebox.showwarning("Advertencia", "Por favor ingrese nombres para el origen y destino.")
            return

        # Verificar si el origen es un aeropuerto
        origin_is_airport = origin_name.startswith(("LE", "LF"))
        if origin_is_airport:
            origin_airport = get_navairport_by_name(espacio_aereo, origin_name)
            if not origin_airport:
                path_text.insert(tk.END, f"ERROR: No se encontró ningún aeropuerto con el código '{origin_name}'.\n")
                path_text.insert(tk.END, "Por favor verifique que el código del aeropuerto de origen sea correcto.\n")
                return
            origin = origin_name  # Usamos el código del aeropuerto directamente
        else:
            # Buscar como punto de navegación normal
            origin = get_navpoint_by_name(espacio_aereo, origin_name)
            if not origin:
                path_text.insert(tk.END, f"ERROR: No se encontró ningún punto con el nombre '{origin_name}'.\n")
                path_text.insert(tk.END, "Por favor verifique que el nombre del punto de origen sea correcto.\n")
                return

        # Verificar si el destino es un aeropuerto
        dest_is_airport = dest_name.startswith(("LE", "LF"))
        if dest_is_airport:
            dest_airport = get_navairport_by_name(espacio_aereo, dest_name)
            if not dest_airport:
                path_text.insert(tk.END, f"ERROR: No se encontró ningún aeropuerto con el código '{dest_name}'.\n")
                path_text.insert(tk.END, "Por favor verifique que el código del aeropuerto de destino sea correcto.\n")
                return
            dest = dest_name  # Usamos el código del aeropuerto directamente
        else:
            # Buscar como punto de navegación normal
            dest = get_navpoint_by_name(espacio_aereo, dest_name)
            if not dest:
                path_text.insert(tk.END, f"ERROR: No se encontró ningún punto con el nombre '{dest_name}'.\n")
                path_text.insert(tk.END, "Por favor verifique que el nombre del punto de destino sea correcto.\n")
                return

        # Si son puntos de navegación normales, verificar si tienen segmentos conectados
        if not origin_is_airport and not dest_is_airport:
            origin_has_segments = False
            dest_has_segments = False
            
            for segment in espacio_aereo.navsegments:
                if segment.origin_number == origin.number or segment.destination_number == origin.number:
                    origin_has_segments = True
                if segment.origin_number == dest.number or segment.destination_number == dest.number:
                    dest_has_segments = True
            
            if not origin_has_segments:
                path_text.insert(tk.END, f"ERROR: El punto '{origin.name}' no está conectado a ningún segmento.\n")
                path_text.insert(tk.END, "Este punto está aislado en el grafo de navegación y no puede ser utilizado para ruteo.\n")
                return
            
            if not dest_has_segments:
                path_text.insert(tk.END, f"ERROR: El punto '{dest.name}' no está conectado a ningún segmento.\n")
                path_text.insert(tk.END, "Este punto está aislado en el grafo de navegación y no puede ser utilizado para ruteo.\n")
                return

        # Mensaje personalizado según los tipos de origen y destino
        if origin_is_airport and dest_is_airport:
            path_text.insert(tk.END, f"Buscando rutas alternativas del aeropuerto {origin_name} al aeropuerto {dest_name} usando algoritmo A*...\n\n")
        elif origin_is_airport:
            path_text.insert(tk.END, f"Buscando rutas alternativas del aeropuerto {origin_name} al punto {dest_name} usando algoritmo A*...\n\n")
        elif dest_is_airport:
            path_text.insert(tk.END, f"Buscando rutas alternativas del punto {origin_name} al aeropuerto {dest_name} usando algoritmo A*...\n\n")
        else:
            path_text.insert(tk.END, f"Buscando rutas alternativas de {origin_name} a {dest_name} usando algoritmo A*...\n\n")

        # Encontrar múltiples rutas usando A*
        rutas = find_multiple_paths_astar(espacio_aereo, origin, dest)

        if not rutas:
            path_text.insert(tk.END, "No se encontraron rutas entre estos puntos.\n")
            if origin_is_airport or dest_is_airport:
                path_text.insert(tk.END, "Esto puede deberse a que no existen SIDs o STARs que permitan conectar los aeropuertos,\n")
                path_text.insert(tk.END, "o a que se encuentran en componentes desconectados del grafo de navegación.\n")
            else:
                path_text.insert(tk.END, "Esto puede deberse a que se encuentran en componentes desconectados del grafo.\n")
            return

        # Almacenar las rutas para su posterior exportación
        app.rutas_alternativas = []

        # Mostrar cada ruta encontrada
        for i, (distancia, ruta_nums) in enumerate(rutas):
            if not isinstance(ruta_nums, list) or not isinstance(distancia, (int, float)):
                continue

            # Convertir números de puntos a objetos NavPoint
            ruta = []
            for num in ruta_nums:
                navpoint = get_navpoint_by_number(espacio_aereo, num)
                if navpoint:
                    ruta.append(navpoint)

            if len(ruta) != len(ruta_nums):
                continue  # Si algún punto no se encontró, saltamos esta ruta

            # Almacenar la ruta
            app.rutas_alternativas.append((ruta, distancia))

            # Mostrar información de la ruta
            path_text.insert(tk.END, f"\nRuta {i+1}:\n")
            path_text.insert(tk.END, f"Distancia: {float(distancia):.2f} km\n")
            path_text.insert(tk.END, "Puntos de la ruta:\n")

            for punto in ruta:
                path_text.insert(tk.END, f"- {punto.name} (#{punto.number})\n")

            # Crear botón para ver esta ruta
            btn_frame = tk.Frame(frame_botones, bg=app.tema["bg"])
            btn_frame.pack(side=tk.LEFT, padx=5)

            tk.Button(
                btn_frame,
                text=f"Ver Ruta {i+1}",
                command=lambda r=ruta: mostrar_espacio_aereo(app, ruta=r),
                bg=app.tema["button_bg"],
                fg=app.tema["button_fg"],
                font=("Segoe UI", 10)
            ).pack(side=tk.LEFT, padx=2)

            # Botón para exportar esta ruta específica
            tk.Button(
                btn_frame,
                text=f"Exportar Ruta {i+1}",
                command=lambda r=ruta: exportar_ruta_a_google_earth_helper(app, r),
                bg=app.tema["button_bg"],
                fg=app.tema["button_fg"],
                font=("Segoe UI", 10)
            ).pack(side=tk.LEFT, padx=2)

    except Exception as e:
        messagebox.showerror("Error", f"Error al buscar rutas: {str(e)}")

def calcular_distancia_ruta(ruta):
    distancia_total = 0
    for i in range(len(ruta) - 1):
        distancia_total += calcular_distancia_entre_puntos(ruta[i], ruta[i+1])
    return distancia_total

def calcular_distancia_entre_puntos(point1, point2):
    import math

    # Convertir grados a radianes
    lat1_rad = math.radians(point1.latitude)
    lon1_rad = math.radians(point1.longitude)
    lat2_rad = math.radians(point2.latitude)
    lon2_rad = math.radians(point2.longitude)

    # Radio de la Tierra en kilómetros
    R = 6371.0

    # Fórmula Haversine
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

# Funciones de integración con Google Earth
def exportar_a_google_earth(app, ruta=None, punto_destacado=None, vecinos=None):
    """Exporta el espacio aéreo completo a Google Earth si no hay ruta especificada"""
    global espacio_aereo

    if not espacio_aereo:
        messagebox.showwarning("Advertencia", "No hay datos de espacio aéreo cargados. Por favor cargue los datos primero.")
        return

    if ruta:
        exportar_ruta_a_google_earth_helper(app, ruta)
    elif punto_destacado and vecinos:
        # Exportar vecinos directamente
        try:
            # Crear contenido KML
            kml_content = generate_neighbors_kml(punto_destacado, vecinos, espacio_aereo)
            
            # Solicitar ubicación para guardar
            filename = filedialog.asksaveasfilename(
                defaultextension=".kml",
                filetypes=[("Archivos KML", "*.kml"), ("Todos los archivos", "*.*")],
                title=f"Guardar vecinos de {punto_destacado.name} como KML"
            )
            
            if not filename:
                return  # Usuario canceló el diálogo
                
            # Asegurarse de que el archivo tenga extensión .kml
            if not filename.lower().endswith('.kml'):
                filename += '.kml'
                
            # Guardar el archivo
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
                
            messagebox.showinfo("Éxito", f"Vecinos de {punto_destacado.name} exportados a {filename}")
            
            # Preguntar si quiere abrir en Google Earth
            if messagebox.askyesno("Abrir en Google Earth", "¿Desea abrir el archivo en Google Earth?"):
                try:
                    os.startfile(filename)
                except Exception as e:
                    messagebox.showwarning("Error", f"No se pudo abrir Google Earth automáticamente: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar vecinos: {str(e)}")
    else:
        # Exportar todo el espacio aéreo
        kml_content = generate_airspace_kml(espacio_aereo)

        # Solicitar ubicación para guardar
        filename = filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=[("Archivos KML", "*.kml"), ("Todos los archivos", "*.*")],
            title="Guardar espacio aéreo como KML"
        )

        if filename:
            # Asegurarse de que el archivo tenga extensión .kml
            if not filename.lower().endswith('.kml'):
                filename += '.kml'
                
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(kml_content)
                messagebox.showinfo("Éxito", f"Espacio aéreo exportado a {filename}")

                # Preguntar si quiere abrir en Google Earth
                if messagebox.askyesno("Abrir en Google Earth", "¿Desea abrir el archivo en Google Earth?"):
                    try:
                        os.startfile(filename)
                    except Exception as e:
                        messagebox.showwarning("Error", f"No se pudo abrir Google Earth automáticamente: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")

def exportar_vecinos_a_google_earth(app, nav_point):
    global espacio_aereo
    
    nav_name = nav_point.get().strip()
    
    if not nav_name:
        messagebox.showwarning("Advertencia", "Por favor ingrese un nombre de punto de navegación.")
        return
        
    # Intentar obtener el punto de navegación
    found_point = get_navpoint_by_name(espacio_aereo, nav_name)
    
    if not found_point:
        messagebox.showwarning("Advertencia", f"Punto de navegación '{nav_name}' no encontrado.")
        return
        
    # Buscar vecinos del punto
    vecinos = []
    for segment in espacio_aereo.navsegments:
        if get_origin_number(segment) == found_point.number:
            destination_number = get_destination_number(segment)
            if destination_number in espacio_aereo.navpoints:
                vecino = espacio_aereo.navpoints[destination_number]
                distancia = get_distance(segment)
                vecinos.append((vecino, distancia))
                
    if not vecinos:
        messagebox.showwarning("Advertencia", f"No se encontraron vecinos para '{nav_name}'.")
        return
    
    # Verificar si tenemos vecinos antes de intentar exportar
    if not vecinos:
        messagebox.showwarning("Advertencia", f"No se encontraron vecinos para '{nav_name}'.")
        return
    
    try:
        # Crear contenido KML directamente aquí
        kml_content = generate_neighbors_kml(found_point, vecinos, espacio_aereo)
        
        # Solicitar ubicación para guardar
        filename = filedialog.asksaveasfilename(
            defaultextension=".kml",
            filetypes=[("Archivos KML", "*.kml"), ("Todos los archivos", "*.*")],
            title=f"Guardar vecinos de {nav_name} como KML"
        )
        
        if not filename:
            return  # Usuario canceló el diálogo
            
        # Asegurarse de que el archivo tenga extensión .kml
        if not filename.lower().endswith('.kml'):
            filename += '.kml'
            
        # Guardar el archivo
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            messagebox.showinfo("Éxito", f"Vecinos de {nav_name} exportados a {filename}")
            
            # Preguntar si quiere abrir en Google Earth
            if messagebox.askyesno("Abrir en Google Earth", "¿Desea abrir el archivo en Google Earth?"):
                try:
                    os.startfile(filename)
                except Exception as e:
                    messagebox.showwarning("Error", f"No se pudo abrir Google Earth automáticamente: {str(e)}\nPor favor, abra el archivo manualmente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al generar el KML: {str(e)}")

def exportar_ruta_a_google_earth(app, origin_point, dest_point):
    global espacio_aereo

    if not espacio_aereo:
        messagebox.showwarning("Advertencia", "No hay datos de espacio aéreo cargados.")
        return

    origin_name = origin_point.get().strip()
    dest_name = dest_point.get().strip()

    if not origin_name or not dest_name:
        messagebox.showwarning("Advertencia", "Por favor ingrese ambos puntos de origen y destino.")
        return

    origin = get_navpoint_by_name(espacio_aereo, origin_name)
    destination = get_navpoint_by_name(espacio_aereo, dest_name)

    if not origin:
        messagebox.showwarning("Advertencia", f"Punto de origen '{origin_name}' no encontrado.")
        return

    if not destination:
        messagebox.showwarning("Advertencia", f"Punto de destino '{dest_name}' no encontrado.")
        return

    # Usar el algoritmo A* para encontrar la ruta
    path_points, total_distance = find_shortest_path_astar(espacio_aereo, origin, dest)

    if not path_points:
        messagebox.showwarning("Advertencia", "No se encontró ninguna ruta entre estos puntos.")
        return

    # Mostrar la ruta en el mapa
    mostrar_espacio_aereo(app, ruta=path_points)

    # Guardar la ruta para exportación posterior
    app.last_path_data = (path_points, total_distance)

    # Exportar ruta a Google Earth
    exportar_ruta_a_google_earth_helper(app, path_points)

def exportar_ruta_a_google_earth_helper(app, ruta):
    """Función auxiliar para exportar ruta a Google Earth"""
    if not ruta or len(ruta) < 2:
        messagebox.showwarning("Advertencia", "No hay una ruta válida para exportar.")
        return

    # Crear contenido KML
    path_name = f"Ruta de {ruta[0].name} a {ruta[-1].name}"
    kml_content = generate_path_kml(path_name, ruta)

    # Solicitar ubicación para guardar
    filename = filedialog.asksaveasfilename(
        defaultextension=".kml",
        filetypes=[("KML files", "*.kml"), ("All files", "*.*")],
        title="Guardar Ruta como KML"
    )

    if filename:
        # Asegurarse de que el archivo tenga extensión .kml
        if not filename.lower().endswith('.kml'):
            filename += '.kml'
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            messagebox.showinfo("Éxito", f"Ruta exportada a {filename}")
            
            # Preguntar si quiere abrir en Google Earth
            if messagebox.askyesno("Abrir en Google Earth", "¿Desea abrir el archivo en Google Earth?"):
                try:
                    os.startfile(filename)
                except:
                    messagebox.showwarning("Error", "No se pudo abrir Google Earth automáticamente. Por favor, abra el archivo manualmente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")

def reproducir_musica_directa(app=None):
    """Inicia la reproducción de música directamente, sin comprobar estado previo."""
    global reproductor_musica

    try:
        # Inicializar el reproductor si no existe
        if reproductor_musica is None:
            reproductor_musica = inicializar_reproductor_musica()
            if reproductor_musica is None:
                if app:
                    app.status.config(text="Error: No se pudo inicializar el reproductor de música")
                messagebox.showerror("Error", "No se pudo inicializar el reproductor de música")
                return
        
        # Intentar reproducir música (forzar detener primero para reiniciar)
        music_generator.detener()
        exito = music_generator.reproducir_cancion_de_carpeta()
        
        if not exito:
            # Si no hay archivos, intentar con sonido generado
            music_generator.crear_sonido()
            exito = music_generator.reproducir()
        
        # Actualizar interfaz basado en el resultado
        if app:
            if exito:
                app.status.config(text="Reproduciendo música")
                app.music_button.config(text="Detener Música", bg="#E53935", 
                                       command=lambda: detener_musica(app))
            else:
                app.status.config(text="Error: No se pudo reproducir música")
                
    except Exception as e:
        mensaje = f"Error al reproducir música: {str(e)}"
        if app:
            app.status.config(text=mensaje)
        print(mensaje)

def detener_musica(app=None):
    """Detiene la reproducción de música."""
    global reproductor_musica
    
    try:
        music_generator.detener()
        
        # Actualizar interfaz
        if app:
            app.status.config(text="Música detenida")
            app.music_button.config(text="Reproducir Música", bg="#1E88E5", 
                                   command=lambda: reproducir_musica_directa(app))
            
    except Exception as e:
        mensaje = f"Error al detener música: {str(e)}"
        if app:
            app.status.config(text=mensaje)
        print(mensaje)

def inicializar_reproductor_musica():
    """Inicializa el reproductor de música y carga un archivo de música."""
    global reproductor_musica

    # Inicializar el reproductor si no existe
    if reproductor_musica is None:
        # Asegurarse que existe la carpeta de música
        music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
        if not os.path.exists(music_folder):
            try:
                os.makedirs(music_folder)
                print(f"Carpeta de música creada: {music_folder}")
            except Exception as e:
                print(f"Error al crear carpeta de música: {str(e)}")
                
        # Inicializar componentes de pygame
        music_generator.inicializar_reproductor()
        
        # Crear la instancia del reproductor
        reproductor_musica = MusicPlayer()
        
        # Intentar cargar una canción de la carpeta
        files_exist = music_generator.reproducir_cancion_de_carpeta()
        
        # Si no se encontraron archivos, detener inmediatamente para que comience detenido
        if not files_exist:
            music_generator.detener()

    return reproductor_musica

def toggle_musica(app=None):
    """Alterna entre reproducir y detener la música."""
    global reproductor_musica

    try:
        # Inicializar el reproductor si no existe
        if reproductor_musica is None:
            reproductor_musica = inicializar_reproductor_musica()
            if reproductor_musica is None:
                if app:
                    app.status.config(text="Error: No se pudo inicializar el reproductor de música")
                messagebox.showerror("Error", "No se pudo inicializar el reproductor de música")
                return
        
        # Comprobar el texto del botón para determinar qué acción realizar
        reproducir = True  # Por defecto, intentamos reproducir música
        
        if hasattr(app, 'music_button'):
            boton_texto = app.music_button.cget("text")
            # Si el botón dice "Detener Música", entonces detenemos
            if boton_texto == "Detener Música":
                reproducir = False
        
        # Ejecutar la acción correspondiente
        if reproducir:
            # Reproducir música
            exito = music_generator.reproducir_cancion_de_carpeta()
            
            if exito:
                # Actualizar la interfaz
                if app:
                    app.status.config(text="Reproduciendo música")
                    if hasattr(app, 'music_button'):
                        app.music_button.config(text="Detener Música", bg="#E53935")
                print("Reproduciendo música")
            else:
                # Intentar con sonido generado como respaldo
                music_generator.crear_sonido()
                exito = music_generator.reproducir()
                
                if exito:
                    if app:
                        app.status.config(text="Reproduciendo música generada")
                        if hasattr(app, 'music_button'):
                            app.music_button.config(text="Detener Música", bg="#E53935")
                    print("Reproduciendo música generada")
                else:
                    if app:
                        app.status.config(text="Error: No se pudo reproducir música")
                    print("Error: No se pudo reproducir música")
        else:
            # Detener música
            music_generator.detener()
            
            # Actualizar la interfaz
            if app:
                app.status.config(text="Música detenida")
                if hasattr(app, 'music_button'):
                    app.music_button.config(text="Reproducir Música", bg="#1E88E5")
            print("Música detenida")

    except Exception as e:
        mensaje = f"Error al controlar la música: {str(e)}"
        if app:
            app.status.config(text=mensaje)
        print(mensaje)

def toggle_tema(app):
    try:
        # Cambiar el tema actual
        app.tema_oscuro = not app.tema_oscuro
        tema = DARK_THEME if app.tema_oscuro else LIGHT_THEME

        # Actualizar el tema de la aplicación
        app.tema = tema
        app.configure(bg=tema["bg"])

        # Actualizar todos los widgets recursivamente
        update_widget_theme(app.main_frame, tema)

        # Actualizar el botón de tema
        if app.tema_oscuro:
            app.theme_button.config(text="☀️ Modo Claro", bg=tema["button_bg"], fg=tema["button_fg"])
        else:
            app.theme_button.config(text="🌙 Modo Oscuro", bg=tema["button_bg"], fg=tema["button_fg"])

        # Actualizar el botón de música si existe
        if hasattr(app, 'music_button'):
            from music_generator import playing
            if playing:
                app.music_button.config(text="Detener Música", bg="#E53935", fg="white")
            else:
                app.music_button.config(text="Reproducir Música", bg=tema["button_bg"], fg=tema["button_fg"])

        # Actualizar las instrucciones
        if hasattr(app, 'instructions'):
            app.instructions.config(bg=tema["bg"], fg=tema["fg"])

        # Mostrar mensaje de estado
        if app.tema_oscuro:
            app.status.config(text="Tema oscuro activado")
        else:
            app.status.config(text="Tema claro activado")

    except Exception as e:
        print(f"Error al cambiar el tema: {str(e)}")
        if hasattr(app, 'status'):
            app.status.config(text=f"Error al cambiar el tema: {str(e)}")

def update_widget_theme(widget, tema):
    try:
        if isinstance(widget, tk.Button):
            if widget.cget("text") == "Detener Música":
                # No cambiar el botón de detener música
                pass
            else:
                widget.config(bg=tema["button_bg"], fg=tema["button_fg"])
        elif isinstance(widget, tk.Label):
            widget.config(bg=tema["bg"], fg=tema["fg"])
        elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
            widget.config(bg=tema["text_bg"], fg=tema["text_fg"], insertbackground=tema["fg"])
        elif isinstance(widget, tk.Frame):
            widget.config(bg=tema["bg"])
            # Actualizar widgets dentro de frames
            for child in widget.winfo_children():
                update_widget_theme(child, tema)
        elif isinstance(widget, ttk.Frame) or isinstance(widget, ttk.LabelFrame):
            # No podemos cambiar directamente el fondo de widgets ttk
            # pero podemos actualizar sus hijos
            for child in widget.winfo_children():
                update_widget_theme(child, tema)
        elif isinstance(widget, ttk.Button):
            # No podemos cambiar directamente el color de los botones ttk
            pass
        elif isinstance(widget, ttk.Label):
            # Intentar actualizar el estilo del label ttk
            style_name = widget.cget("style") or "TLabel"
            widget.configure(style=style_name)
    except Exception as e:
        print(f"Error al actualizar widget {widget}: {str(e)}")

def mostrar_info_equipo(app):
    info_window = tk.Toplevel(app)
    info_window.title("Información del Equipo")
    info_window.geometry("600x500")
    info_window.configure(bg=app.tema["bg"])

    # Marco principal
    main_frame = tk.Frame(info_window, bg=app.tema["bg"])
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Título
    title_label = tk.Label(
        main_frame,
        text="Equipo de Desarrollo",
        font=(app.tema["font_family"], app.tema["font_size_header"], "bold"),
        bg=app.tema["bg"],
        fg=app.tema["fg"]
    )
    title_label.pack(pady=(0, 20))

    # Información del equipo
    info_text = "Este proyecto ha sido desarrollado por:\n\n"
    info_text += "• Saoussane Ziati\n"
    info_text += "• Iu Serret\n"
    info_text += "• Alex Millán"

    info_label = tk.Label(
        main_frame,
        text=info_text,
        font=(app.tema["font_family"], app.tema["font_size_normal"]),
        justify=tk.LEFT,
        bg=app.tema["bg"],
        fg=app.tema["fg"]
    )
    info_label.pack(pady=(0, 20), anchor=tk.W)

    # Intenta cargar y mostrar la imagen del equipo
    try:
        img = Image.open("grupo_trabajo.jpg")

        # Aplicar efecto de desenfoque
        img = img.filter(ImageFilter.BLUR)

        # Redimensionar la imagen manteniendo la proporción
        basewidth = 400
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img)

        # Crear un panel para la imagen
        img_panel = tk.Label(main_frame, image=photo, bg=app.tema["bg"])
        img_panel.image = photo  # Mantener una referencia para evitar que se elimine
        img_panel.pack(pady=10)
    except Exception as e:
        error_label = tk.Label(
            main_frame,
            text=f"No se pudo cargar la imagen: {str(e)}",
            font=("Segoe UI", 10),
            fg="red",
            bg=app.tema["bg"]
        )
        error_label.pack(pady=10)

def debug_airport_info(app, path_text):
    """Muestra información de depuración sobre aeropuertos."""
    path_text.delete(1.0, tk.END)
    
    # Mostrar todos los aeropuertos en el espacio aéreo
    path_text.insert(tk.END, "INFORMACIÓN DE AEROPUERTOS:\n\n")
    
    if not espacio_aereo.navairports:
        path_text.insert(tk.END, "No hay aeropuertos cargados en el espacio aéreo.\n")
        return
    
    path_text.insert(tk.END, f"Total de aeropuertos cargados: {len(espacio_aereo.navairports)}\n\n")
    
    for code, airport in espacio_aereo.navairports.items():
        path_text.insert(tk.END, f"Aeropuerto: {code}\n")
        
        # Mostrar SIDs
        if airport.sids:
            path_text.insert(tk.END, f"  SIDs ({len(airport.sids)}):\n")
            for sid in airport.sids:
                sid_point = espacio_aereo.navpoints.get(sid)
                if sid_point:
                    path_text.insert(tk.END, f"    - #{sid} ({sid_point.name})\n")
                else:
                    path_text.insert(tk.END, f"    - #{sid} (punto no encontrado)\n")
        else:
            path_text.insert(tk.END, "  No tiene SIDs definidos\n")
        
        # Mostrar STARs
        if airport.stars:
            path_text.insert(tk.END, f"  STARs ({len(airport.stars)}):\n")
            for star in airport.stars:
                star_point = espacio_aereo.navpoints.get(star)
                if star_point:
                    path_text.insert(tk.END, f"    - #{star} ({star_point.name})\n")
                else:
                    path_text.insert(tk.END, f"    - #{star} (punto no encontrado)\n")
        else:
            path_text.insert(tk.END, "  No tiene STARs definidos\n")
        
        path_text.insert(tk.END, "\n")

def menu_file(app):
    """Crea el menú Archivo."""
    file_menu = tk.Menu(app.menu, tearoff=0)
    file_menu.add_command(label="Cargar datos", command=lambda: cargar_datos(app))
    file_menu.add_command(label="Guardar Ruta", command=lambda: guardar_ruta(app))
    file_menu.add_command(label="Exportar a Google Earth", command=lambda: exportar_a_google_earth(app))
    file_menu.add_separator()
    file_menu.add_command(label="Información de Aeropuertos", command=lambda: debug_airport_info(app, app.path_text))
    file_menu.add_separator()
    file_menu.add_command(label="Salir", command=app.quit)
    app.menu.add_cascade(label="Archivo", menu=file_menu)

class AplicacionNavegacionEspacioAereo(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Detectar sistema operativo
        self.sistema_operativo = platform.system()
        
        # Configuración general de la ventana
        self.title("FlyPath")
        self.geometry("800x700")  # Tamaño inicial más grande

        # Inicializar tema
        self.tema_oscuro = False
        self.tema = LIGHT_THEME
        self.configure(bg=self.tema["bg"])
        
        # Configurar estilos
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Usar un tema base que permita personalización
        self.style.configure("TLabel", background=self.tema["bg"], foreground=self.tema["fg"])
        self.style.configure("TButton", background=self.tema["button_bg"], foreground=self.tema["button_fg"])

        # Configurar estilo para LabelFrame sin borde y con fondo igual al fondo principal
        self.style.configure("TLabelFrame", background=self.tema["bg"], foreground=self.tema["fg"])
        self.style.configure("TLabelFrame.Label", background=self.tema["bg"], foreground=self.tema["fg"], 
                            font=(self.tema["font_family"], 11, "bold"))

        # Quitar el borde del LabelFrame
        self.style.layout("TLabelFrame", [
            ("LabelFrame.border", {
                "sticky": "nswe",
                "children": [
                    ("LabelFrame.padding", {
                        "sticky": "nswe",
                        "children": [
                            ("LabelFrame.label", {"side": "top", "sticky": ""}),
                            ("LabelFrame.children", {"sticky": "nswe"})
                        ]
                    })
                ]
            })
        ])

        self.style.configure("Instructions.TLabel", font=(self.tema["font_family"], self.tema["font_size_normal"]), 
                             background=self.tema["bg"], foreground=self.tema["fg"])

        try:
            # Intentar establecer un icono para la ventana
            self.iconbitmap("icon.ico")
        except:
            # Si no se encuentra el icono, continuar sin él
            pass

        # Enable high DPI awareness for sharper rendering on Windows
        try:
            from ctypes import windll
            if self.sistema_operativo == 'Windows':
                windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        self.main_frame = tk.Frame(self, bg=self.tema["bg"])
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Crear un encabezado moderno
        header_frame = tk.Frame(self.main_frame, bg="#2c3e50", height=60)
        header_frame.pack(fill="x", pady=(0, 20))
        header_label = tk.Label(header_frame, text="FlyPath: Sistema de Navegación Aérea",
                              font=(self.tema["font_family"], self.tema["font_size_header"], "bold"), fg="white", bg="#2c3e50")
        header_label.pack(pady=15)

        # Usar widgets con tema para mejor apariencia
        style = ttk.Style()
        style.configure("TButton", padding=10)
        style.configure("TLabelFrame", background=self.tema["bg"])
        style.configure("TLabel", background=self.tema["bg"])

        load_frame = tk.Frame(self.main_frame, bg=self.tema["bg"], highlightthickness=0)
        load_frame.pack(fill="x", pady=10)

        load_label = tk.Label(load_frame, text="Cargar y Visualizar Datos",
                              font=(self.tema["font_family"], self.tema["font_size_title"], "bold"), bg=self.tema["bg"], fg=self.tema["fg"])
        load_label.pack(anchor="w", pady=(0, 10))

        buttons_frame = tk.Frame(load_frame, bg=self.tema["bg"])
        buttons_frame.pack(fill="x", pady=5)

        # Botón para cargar archivos
        load_button = tk.Button(
            buttons_frame,
            text="Cargar Archivos",
            command=lambda: cargar_espacio_aereo(self),
            bg=self.tema["button_bg"],
            fg=self.tema["button_fg"],
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"  # Cambia el cursor al pasar sobre el botón
        )
        load_button.pack(side=tk.LEFT, padx=5)

        # Botón para visualizar el mapa
        visualize_button = tk.Button(
            buttons_frame,
            text="Visualizar Mapa",
            command=lambda: mostrar_espacio_aereo(self),
            bg=self.tema["button_bg"],
            fg=self.tema["button_fg"],
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"  # Cambia el cursor al pasar sobre el botón
        )
        visualize_button.pack(side=tk.LEFT, padx=5)

        # Configure style for accent buttons
        style.configure("Accent.TButton", font=("Helvetica", 11, "bold"))

        analysis_frame = tk.Frame(self.main_frame, bg=self.tema["bg"], highlightthickness=0)
        analysis_frame.pack(fill="x", pady=10)

        analysis_label = tk.Label(analysis_frame, text="Herramientas de Análisis",
                              font=(self.tema["font_family"], self.tema["font_size_title"], "bold"), bg=self.tema["bg"], fg=self.tema["fg"])
        analysis_label.pack(anchor="w", pady=(0, 10))

        analysis_buttons_frame = tk.Frame(analysis_frame, bg=self.tema["bg"])
        analysis_buttons_frame.pack(fill="x", pady=5)

        # Botón para encontrar vecinos
        neighbors_button = tk.Button(
            analysis_buttons_frame,
            text="Encontrar Vecinos",
            command=lambda: mostrar_vecinos(self),
            bg=self.tema["button_bg"],
            fg=self.tema["button_fg"],
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"  # Cambia el cursor al pasar sobre el botón
        )
        neighbors_button.pack(side=tk.LEFT, padx=5)

        # Botón para encontrar ruta óptima
        path_button = tk.Button(
            analysis_buttons_frame,
            text="Encontrar Ruta",
            command=lambda: encontrar_ruta(self),
            bg=self.tema["button_bg"],
            fg=self.tema["button_fg"],
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"  # Cambia el cursor al pasar sobre el botón
        )
        path_button.pack(side=tk.LEFT, padx=5)

        # Add export frame for KML functionality
        export_frame = tk.Frame(self.main_frame, bg=self.tema["bg"], highlightthickness=0)
        export_frame.pack(fill="x", pady=10)

        export_label = tk.Label(export_frame, text="Exportar a Google Earth",
                              font=(self.tema["font_family"], self.tema["font_size_title"], "bold"), bg=self.tema["bg"], fg=self.tema["fg"])
        export_label.pack(anchor="w", pady=(0, 10))

        export_buttons_frame = tk.Frame(export_frame, bg=self.tema["bg"])
        export_buttons_frame.pack(fill="x", pady=5)

        # Botón para exportar mapa
        export_map_button = tk.Button(
            export_buttons_frame,
            text="Exportar Mapa",
            command=lambda: exportar_a_google_earth(self),
            bg=self.tema["button_bg"],
            fg=self.tema["button_fg"],
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"  # Cambia el cursor al pasar sobre el botón
        )
        export_map_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Etiqueta moderna de instrucciones
        self.instructions = tk.Label(
            self.main_frame,
            text="Instrucciones: Cargue los datos del espacio aéreo y elija una opción.",
            wraplength=600,
            justify="center",
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            bg=self.tema["bg"],
            fg=self.tema["fg"],
            pady=10
        )
        self.instructions.pack(pady=15, fill="x")

        # Botón de música directamente en el main_frame (no en un frame separado)
        self.music_button = tk.Button(
            self.main_frame,
            text="Reproducir Música",
            command=lambda: reproducir_musica_directa(self),
            bg="#1E88E5",  # Azul más suave
            fg="white",
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"]
        )
        self.music_button.pack(side=tk.LEFT, anchor=tk.SW, padx=20, pady=10)

        # Botón para cambiar el tema (en la esquina inferior derecha)
        self.theme_button = tk.Button(
            self.main_frame,
            text="🌙 Modo Oscuro",
            command=lambda: toggle_tema(self),
            bg=self.tema["button_bg"],
            fg=self.tema["button_fg"],
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"  # Cambia el cursor al pasar sobre el botón
        )
        self.theme_button.pack(side=tk.RIGHT, padx=20, pady=10)

        # Botón para mostrar información del equipo
        self.info_button = tk.Button(
            self.main_frame,
            text="ℹ️ Info Equipo",
            command=lambda: mostrar_info_equipo(self),
            bg="#3498db",  # Azul claro
            fg="white",
            font=(self.tema["font_family"], self.tema["font_size_normal"]),
            padx=self.tema["button_padx"],
            pady=self.tema["button_pady"],
            relief=self.tema["relief"],
            borderwidth=self.tema["borderwidth"],
            cursor="hand2"
        )
        self.info_button.pack(side=tk.RIGHT, padx=5, pady=10)
        
        # Barra de estado mejorada
        self.status = tk.Label(self.main_frame, text="Listo", bd=2, relief=tk.SUNKEN, 
                              anchor=tk.W, bg=self.tema["status_bg"], fg=self.tema["status_fg"], 
                              font=(self.tema["font_family"], 9))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Almacenar datos para exportación
        self.last_neighbors_data = None
        self.last_path_data = None

        global espacio_aereo
        espacio_aereo = None
        
def main():
    app = AplicacionNavegacionEspacioAereo()
    app.mainloop()

if __name__ == "__main__":
    main()
