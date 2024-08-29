#%% IMPORT 
import sys
from PyQt5.QtCore import Qt, QCoreApplication
# Définir les attributs d'application nécessaires avant la création de QApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView  # Import après Qt.AA_ShareOpenGLContexts
from PyQt5.QtGui import QFont


import h5py
import numpy as np
import matplotlib.pyplot as plt 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import folium


h5_file_path = None  # Global variable to store the .h5 file path
graph_widget = None  # Matplotlib widget for the graph
map_widget = None  # Folium widget for the map
current_id = 0  # Variable to store the current ID
nb_points = 0  # Total number of points available

map_window = None

#%%
def print_structure(name, obj):
    if isinstance(obj, h5py.Dataset):
        print(f"Dataset: {name}")
    elif isinstance(obj, h5py.Group):
        print(f"Group: {name}")

def create_matplotlib_widget(i, parent=None):
    fig, ax = plt.subplots()
    canvas = FigureCanvas(fig)
    plot_data(ax, i)
    return canvas

def plot_data(ax, i):
    global h5_file_path
    if h5_file_path is None:
        QMessageBox.warning(None, "Error", "No .h5 file has been loaded.")
        return
    with h5py.File(h5_file_path, 'r') as file:
        file.visititems(print_structure)
        dataset_name = 'df/rxwaveform'
        data_wave = file[dataset_name][:]

    # Données d'entrée
    data = data_wave[i]
    
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        
    # # Calculer les statistiques de base
    # mean_value = np.mean(data)
    # std_value = np.std(data)
    # max_value = np.max(data)
    # min_value = np.min(data)
    # median_value = np.median(data)
    # q1_value = np.percentile(data, 25)  # Premier quartile
    # q3_value = np.percentile(data, 75)  # Troisième quartile

    # # Afficher les résultats
    # print(f"Mean: {mean_value}")
    # print(f"Standard Deviation: {std_value}")
    # print(f"Maximum: {max_value}")
    # print(f"Minimum: {min_value}")
    # print(f"Median: {median_value}")
    # print(f"First Quartile (Q1): {q1_value}")
    # print(f"Third Quartile (Q3): {q3_value}")    

    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    
    # Étape 1 : Décoder la chaîne d'octets en chaîne de caractères
    decoded_data = data.decode('utf-8')
    
    # Étape 2 : Séparer la chaîne en une liste de sous-chaînes
    string_values = decoded_data.split(',')
    
    # Étape 3 : Convertir chaque sous-chaîne en un nombre flottant
    float_values = [float(value) for value in string_values]
        
    data_wave[i] = float_values

    data_wave_new = data_wave[i]
    x_values = range(len(data_wave_new))  # X values starting from 0
    ax.clear()  # Clear previous plot
    ax.plot(x_values, data_wave_new, color='#1f77b4')  # Blue color for the line
    ax.set_facecolor('#2c3e50')  # Dark background color
    ax.set_title("GEDI WAVEFORM", fontsize=14, fontweight='bold', color='#1f77b4')  # Updated title
    ax.set_xlabel("BINS (ns)", fontsize=12, color='#1f77b4')  # Updated xlabel
    ax.set_ylabel("Amplitude", fontsize=12, color='#1f77b4')
    ax.tick_params(axis='both', which='major', labelsize=10, colors='#1f77b4')  # Blue ticks
    ax.grid(True, color='#34495e')  # Light gray grid color
    ax.figure.tight_layout()
    ax.figure.canvas.draw()  # Update canvas
    plt.close()

def create_map_widget(i, parent=None):
    latitude, longitude, elevation, rh98_a1,Id,alt = generate_coordinates(i)
    if latitude is None or longitude is None:
        QMessageBox.warning(None, "Error", "No .h5 file has been loaded.")
        return QLabel("Error: No .h5 file has been loaded.", alignment=Qt.AlignCenter)

    my_map = folium.Map(location=[latitude, longitude], zoom_start=15)
   
    folium.Circle(
        location=[latitude, longitude],
        radius=25,
        color='#e74c3c',  # Red color for target point
        fill=True,
        fill_color='#e74c3c',
        fill_opacity=0.6
    ).add_to(my_map)

    # Add 9 blue points
    with h5py.File(h5_file_path, 'r') as file:
        dataset_name = 'df/lon_lowestmode'
        data_lon = file[dataset_name][:]
        dataset_name = 'df/lat_lowestmode'
        data_lat = file[dataset_name][:]

        # Show 9 points around the target point
        for index in range(max(0, i-4), min(len(data_lat), i+5)):
            if index != i:
                folium.Circle(
                    location=[data_lat[index], data_lon[index]],
                    radius=25,
                    color='#3498db',
                    fill=True,
                    fill_color='#3498db',
                    fill_opacity=0.6
                ).add_to(my_map)
                

    folium.TileLayer('openstreetmap').add_to(my_map)
    folium.TileLayer('cartodbpositron').add_to(my_map)
    folium.TileLayer('cartodbdark_matter').add_to(my_map)
    folium.TileLayer(
    tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    name='esriworldimagery').add_to(my_map)
    folium.LayerControl().add_to(my_map)

    popup_html = f'''
        <div style="font-family: Arial, sans-serif; font-size: 14px; background-color: #f39c12; color: white; text-align: center; padding: 10px; border-radius: 10px;">
            <h3 style="margin: 0; padding: 0;">ID : {Id}</h3>
            <p><strong>Latitude:</strong> {latitude}</p>
            <p><strong>Longitude:</strong> {longitude}</p>
            <p><strong>Elevation_lowestmode (m):</strong> {elevation}</p>
            <p><strong>rh98_a1 (cm):</strong> {rh98_a1}</p>
            <p><strong>ALT:</strong> {alt}</p>
        </div>
    '''
    popup = folium.Popup(popup_html, max_width=300)
    folium.Marker([latitude, longitude], popup=popup).add_to(my_map)
   
    view = QWebEngineView()
    view.setHtml(my_map.get_root().render())
    return view

def generate_coordinates(i):
    global h5_file_path
    if h5_file_path is None:
        return None, None

    with h5py.File(h5_file_path, 'r') as file:
        dataset_name = 'df/lon_lowestmode'
        data_lon = file[dataset_name][:]
        lon = data_lon[i]
        dataset_name = 'df/altitude_instrument'
        data_alt = file[dataset_name][:]
        alt = data_alt[i]
        dataset_name = 'df/lat_lowestmode'
        data_lat = file[dataset_name][:]
        lat = data_lat[i]
        dataset_name = 'df/elev_lowestmode'
        data_elev = file[dataset_name][:]
        elev = data_elev[i]
        dataset_name = 'df/rh_a1'
        data_rh98_a1 = file[dataset_name][:, 98]  
        rh98_a1 = data_rh98_a1[i]
        dataset_name = 'df/IDS'
        data_IDS = file[dataset_name][:]
        Id = data_IDS[i]
        Id = Id.decode('utf-8')

    return lat, lon, elev, rh98_a1, Id, alt

def get_nb_points():
    global nb_points, h5_file_path
    if h5_file_path is None:
        nb_points = 0
        return
    with h5py.File(h5_file_path, 'r') as file:
        dataset_name = 'df/elev_lowestmode'
        nb_points = len(file[dataset_name][:])

def setup_ui(window):
    window.setWindowTitle("GEDI MAP VISUALIZATION")
    window.setGeometry(100, 100, 800, 600)

    # CSS styles for the interface
    style_sheet = """
    QWidget {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #3a6186, stop: 1 #89253e);
        color: #ecf0f1;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    QProgressBar {
        border: 1px solid #34495e;
        border-radius: 5px;
        background-color: #2c3e50;
        text-align: center;
        color: #ecf0f1;
    }
    QProgressBar::chunk {
        background-color: #1abc9c;
        width: 5px;
        margin: 0.5px;
    }
    QLabel {
        font-size: 14px;
        color: #e74c3c;
    }
    QLineEdit {
        padding: 8px;
        font-size: 14px;
        border-radius: 5px;
        border: 1px solid #1abc9c;
        background-color: #34495e;
        color: #ecf0f1;
    }
    QPushButton {
        background-color: #3498db;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        font-size: 14px;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #1f618d;
    }
    .quit-button {
        background-color: #e74c3c;
    }
    .quit-button:hover {
        background-color: #c0392b;
    }
    QTabBar::tab {
        background-color: #2c3e50;
        color: #bdc3c7;
        padding: 10px;
        border: 1px solid #34495e;
        border-bottom: none;
    }
    QTabBar::tab:selected {
        background-color: #34495e;
        color: #ecf0f1;
    }
    QTabBar::tab:hover {
        background-color: #3a6186;
    }
    """

    layout = QVBoxLayout()

    # Frame for drag-and-drop
    drag_drop_frame = QFrame()
    drag_drop_frame.setAcceptDrops(True)
    drag_drop_frame.setStyleSheet("QFrame { border: 2px dashed gray; background-color: rgba(255, 255, 255, 0.7); }")
    drag_drop_frame.setMinimumHeight(100)
    drag_drop_label = QLabel("Drop .h5 file here", drag_drop_frame)
    drag_drop_label.setAlignment(Qt.AlignCenter)
    drag_drop_layout = QVBoxLayout(drag_drop_frame)
    drag_drop_layout.addWidget(drag_drop_label)

    drag_drop_frame.dragEnterEvent = lambda event: event.acceptProposedAction() if event.mimeData().hasUrls() else None
    drag_drop_frame.dropEvent = lambda event: handle_drop_event(event, drag_drop_label)

    layout.addWidget(drag_drop_frame)
    
  
    # Input field for ID
    id_input_label = QLabel("Please enter an ID:")
    id_input_label.setFont(QFont("Arial", 14))
    id_input_label.setStyleSheet("color: #1f77b4;")
    id_input = QLineEdit()
    id_input.setPlaceholderText("ID here")
    id_input.setStyleSheet("padding: 8px;color: #1f77b4; font-family: Arial; font-size: 14px; background-color: rgba(255, 255, 255, 0.9); border: 1px solid #cccccc; border-radius: 5px;")

    id_layout = QHBoxLayout()
    id_layout.addWidget(id_input_label)
    id_layout.addWidget(id_input)

    # Add Close button
    quit_button = QPushButton("Close")
    quit_button.clicked.connect(window.close)  # Close the main window
    quit_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; }"
                              "QPushButton:hover { background-color: #c0392b; }")
    id_layout.addWidget(quit_button)

    layout.addLayout(id_layout)

    # Button to generate graph and map
    def on_submit():
        global graph_widget, map_widget, current_id
        try:
            i = id_input.text()
            
            i = i.strip()
            current_id = i
            
            with h5py.File(h5_file_path, 'r') as file:
                dataset_name = 'df/IDS'
                global data_ids
                data_ids = file[dataset_name][:]
                for l in range (len(data_ids)):
                    data_ids[l] = data_ids[l].decode()
             
            for j in range (len(data_ids)):
                if current_id == data_ids[j]:

                    i = j
                    current_id = i
                    
             
                
        except ValueError:
            QMessageBox.warning(None, "Error", "Please enter a valid ID.")
            return
        
        
       
                
        if h5_file_path is None:
            QMessageBox.warning(None, "Error", "No .h5 file has been loaded.")
            return

        # Update graph
        if graph_widget is None:
            graph_widget = create_matplotlib_widget(i)
            layout.addWidget(graph_widget)
        else:
            plot_data(graph_widget.figure.gca(), i)

        # Update map
        new_map_widget = create_map_widget(i)
        if map_widget is None:
            map_widget = new_map_widget
            layout.addWidget(map_widget)
        else:
            layout.removeWidget(map_widget)
            map_widget = new_map_widget
            layout.addWidget(map_widget)

    submit_button = QPushButton("RUN")
    submit_button.setFont(QFont("Arial", 16))
    submit_button.setStyleSheet("QPushButton { background-color: #f39c12; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; }"
                                "QPushButton:hover { background-color: #e67e22; }")
    submit_button.clicked.connect(on_submit)

    random_button = QPushButton("RANDOM")
    random_button.setFont(QFont("Arial", 16))
    random_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; }"
                                "QPushButton:hover { background-color: #45a049; }")

    # Add widgets to layout
    layout.addWidget(submit_button)
    layout.addWidget(random_button)

    # Apply stylesheet
    window.setStyleSheet(style_sheet)

    # Set the main window's layout
    central_widget = QWidget()
    central_widget.setLayout(layout)
    window.setCentralWidget(central_widget)

    def on_random():
        global current_id, nb_points
        with h5py.File(h5_file_path, 'r') as file:
            dataset_name = 'df/IDS'
            global data_ids
            data_ids = file[dataset_name][:]
            for l in range (len(data_ids)):
                data_ids[l] = data_ids[l].decode()
        random_id = np.random.randint(0, nb_points)  # Generate a random ID between 0 and nb_points
        random_id = data_ids[random_id]
        id_input.setText(str(random_id))
        current_id = random_id
        on_submit()

    random_button.clicked.connect(on_random)

    button_layout = QHBoxLayout()
    button_layout.addWidget(submit_button)
    button_layout.addWidget(random_button)
    button_layout.addStretch()

    layout.addLayout(button_layout)

    # Navigation buttons layout
    nav_layout = QHBoxLayout()

    # Button to go to previous ID
    prev_button = QPushButton("< Previous")
    prev_button.setFont(QFont("Arial", 12))
    prev_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 16px; font-size: 12px; border-radius: 5px; }"
                              "QPushButton:hover { background-color: #2980b9; }")

    def on_previous():
        global current_id
        if current_id > 0:
            current_id -= 1
            id_input.setText(data_ids[current_id])
            on_submit()

    prev_button.clicked.connect(on_previous)
    nav_layout.addWidget(prev_button)

    nav_layout.addStretch()
 
    # Button to go to next ID
    next_button = QPushButton("Next >")
    next_button.setFont(QFont("Arial", 12))
    next_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; border: none; padding: 8px 16px; font-size: 12px; border-radius: 5px; }"
                              "QPushButton:hover { background-color: #2980b9; }")

    def on_next():
        global current_id
        current_id += 1
        id_input.setText(data_ids[current_id])
        on_submit()

    next_button.clicked.connect(on_next)
    nav_layout.addWidget(next_button)

    layout.addLayout(nav_layout)

    container = QWidget()
    container.setLayout(layout)
    container.setStyleSheet(style_sheet)

    window.setCentralWidget(container)

    # Enable pressing Enter to submit
    def on_enter_pressed():
        on_submit()

    id_input.returnPressed.connect(on_enter_pressed)

def handle_drop_event(event, label):
    mime_data = event.mimeData()
    if mime_data.hasUrls():
        url = mime_data.urls()[0]
        file_path = url.toLocalFile()
        if file_path.endswith(".h5"):
            global h5_file_path, current_id
            h5_file_path = file_path
            current_id = 0  # Reset current_id when a new file is loaded
            get_nb_points()  # Update nb_points when a new file is loaded
            label.setText(f"File loaded: {file_path}")
        else:
            label.setText("The dropped file is not a .h5 file")


def MAIN() :
    global map_window
    if map_window is None:
        map_window = QMainWindow()
        setup_ui(map_window)
    map_window.show()

