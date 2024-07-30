#%% IMPORT 
import math
import MAP
import sys
import os
import zipfile
import shutil
import h5py
import pandas as pd
from shapely.geometry import Polygon
import geopandas as gp
import numpy as np
import warnings
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QLineEdit, QPushButton, QFileDialog, QMessageBox, QTabWidget, QProgressBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from fastkml import kml
import platform
import webbrowser
warnings.filterwarnings("ignore")
import subprocess

from PyQt5.QtCore import Qt, QCoreApplication
# Définir les attributs d'application nécessaires avant la création de QApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView  # Import après Qt.AA_ShareOpenGLContexts
from PyQt5.QtGui import QFont

import matplotlib.pyplot as plt 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import folium
#%% MAIN WINDOW
# Global variable to hold references to QLineEdit widgets
line_edit_refs = {}

def create_main_window():
    main_window = QMainWindow()
    main_window.setWindowTitle('GEDI Data Processor')
    main_window.setGeometry(100, 100, 800, 600)

    central_widget = QWidget()
    layout = QVBoxLayout()
    main_window.setCentralWidget(central_widget)

    tab_widget = QTabWidget()

    # Tab for DOWNLOAD
    utilities_tab = QWidget()
    utilities_layout = QVBoxLayout()
    utilities_tab.setLayout(utilities_layout)
    
    open_pdf_button = QPushButton("Open User Manual")
    open_pdf_button.clicked.connect(open_pdf_file)
    utilities_layout.addWidget(open_pdf_button)

    open_google_earth_button = QPushButton("Open Google Earth Pro")
    open_google_earth_button.clicked.connect(open_google_earth)
    utilities_layout.addWidget(open_google_earth_button)
    
    open_gedi_website_button = QPushButton("Open GEDI Data Download Page")
    open_gedi_website_button.clicked.connect(open_gedi_website)
    utilities_layout.addWidget(open_gedi_website_button)

    quit_button = QPushButton("Close")
    quit_button.clicked.connect(QApplication.instance().quit)  # Quit the application
    quit_button.setProperty('class', 'quit-button')  # Set the custom class
    utilities_layout.addWidget(quit_button)
    tab_widget.addTab(utilities_tab, "DOWNLOAD")

    # Tab for Drag and Drop Unzipper
    unzip_tab = QWidget()
    unzip_layout = QVBoxLayout()
    unzip_tab.setLayout(unzip_layout)

    unzip_label = QLabel("Drag and drop zip files here to extract .h5 files:")
    unzip_label.setAlignment(Qt.AlignCenter)
    unzip_label.setFont(QFont('Arial', 12))

    unzip_layout.addWidget(unzip_label)
    
    progress_bar = QProgressBar()
    progress_bar.setRange(0, 100)  # Range of progress bar
    progress_bar.setValue(0)  # Initial value
    progress_bar.setAlignment(Qt.AlignCenter)

    unzip_layout.addWidget(progress_bar)
    
    def drag_enter_event(event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def drop_event(event, label):
        urls = event.mimeData().urls()
        if urls:
            for url in urls:
                file_path = url.toLocalFile()
                label.setText(f"File dropped: {file_path}")
                if file_path.endswith('.zip'):
                    extract_h5_from_zip(file_path, label, progress_bar)

    central_widget.dragEnterEvent = lambda event: drag_enter_event(event)
    central_widget.dropEvent = lambda event: drop_event(event, unzip_label)
    central_widget.setAcceptDrops(True)

    tab_widget.addTab(unzip_tab, "Drag and Drop Unzipper")

    # Add Quit button to the unzip_tab
    quit_button = QPushButton("Close")
    quit_button.clicked.connect(QApplication.instance().quit)  # Quit the application
    quit_button.setProperty('class', 'quit-button')  # Set the custom class
    unzip_layout.addWidget(quit_button)

    # Tab for GEDI Data Processor
    gedi_tab = QWidget()
    gedi_layout = QVBoxLayout()
    gedi_tab.setLayout(gedi_layout)
    
    inDirLabel = QLabel("Enter the local directory containing GEDI files to be processed:")
    inDirLineEdit = QLineEdit()
    browseDirButton = QPushButton("Browse")
    browseDirButton.clicked.connect(lambda: browse_directory(inDirLineEdit))

    kmlLabel = QLabel("Select KML file to extract ROI:")
    kmlLineEdit = QLineEdit()
    browseKMLButton = QPushButton("Browse")
    browseKMLButton.clicked.connect(lambda: browse_kml(kmlLineEdit))

    global roiLineEdit
    roiLabel = QLabel("Region of interest (ROI) extracted:")
    roiLineEdit = QLineEdit()
    roiLineEdit.setReadOnly(True)

    # outputFileLabel = QLabel("Enter the output HDF5 file name:")
    outputFileLineEdit = "out.h5"

    beamsLabel = QLabel("Enter specific beams to be included in the output GeoJSON (optional, default is all beams):")
    beamsLineEdit = QLineEdit()

    sdsLabel = QLabel("Enter specific science datasets (SDS) to include in the output GeoJSON (optional):")
    sdsLineEdit = QLineEdit()

    processButton = QPushButton("Process Files")
    processButton.clicked.connect(lambda: process_files(inDirLineEdit, roiLineEdit, outputFileLineEdit, beamsLineEdit, sdsLineEdit))
    
    gedi_layout.addWidget(inDirLabel)
    gedi_layout.addWidget(inDirLineEdit)
    gedi_layout.addWidget(browseDirButton)
    gedi_layout.addWidget(kmlLabel)
    gedi_layout.addWidget(kmlLineEdit)
    gedi_layout.addWidget(browseKMLButton)
    gedi_layout.addWidget(roiLabel)
    gedi_layout.addWidget(roiLineEdit)
    #gedi_layout.addWidget(outputFileLabel)
    #gedi_layout.addWidget(outputFileLineEdit)
    gedi_layout.addWidget(beamsLabel)
    gedi_layout.addWidget(beamsLineEdit)
    gedi_layout.addWidget(sdsLabel)
    gedi_layout.addWidget(sdsLineEdit)
    gedi_layout.addWidget(processButton)
    
    quit_button = QPushButton("Close")
    quit_button.clicked.connect(QApplication.instance().quit)  # Quit the application
    quit_button.setProperty('class', 'quit-button')  # Set the custom class
    gedi_layout.addWidget(quit_button)
    tab_widget.addTab(gedi_tab, "GEDI Data Processor")
    
    # Tab for MAP
    MAP_tab = QWidget()
    MAP_layout = QVBoxLayout()
    MAP_tab.setLayout(MAP_layout)
    map_button = QPushButton("Open Map")
    map_button.clicked.connect(open_map)  # Replace open_map_function with your actual function
    MAP_layout.addWidget(map_button)
    tab_widget.addTab(MAP_tab, "MAP")
    layout.addWidget(tab_widget)
    layout.addStretch()
    quit_button = QPushButton("Close")
    quit_button.clicked.connect(QApplication.instance().quit)  # Quit the application
    quit_button.setProperty('class', 'quit-button')  # Set the custom class
    MAP_layout.addWidget(quit_button)
    central_widget.setLayout(layout)

    # Apply stylesheet
    main_window.setStyleSheet("""
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
        color: #ecf0f1;
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
    """)

    # Store references to line edits
    line_edit_refs['roi'] = roiLineEdit

    return main_window

#%% PROCESSING
def browse_directory(inDirLineEdit):
    dir_name = QFileDialog.getExistingDirectory(None, "Select Directory")
    if dir_name:
        inDirLineEdit.setText(dir_name)

def browse_kml(kmlLineEdit):
    file_name, _ = QFileDialog.getOpenFileName(None, "Select KML File", "", "KML files (*.kml)")
    if file_name:
        kmlLineEdit.setText(file_name)
        extract_roi_from_kml(file_name, line_edit_refs['roi'])

def extract_roi_from_kml(kml_file, roiLineEdit):
    with open(kml_file, 'rb') as f:  # Open the file in binary mode
        k = kml.KML()
        k.from_string(f.read())
        
        features = list(k.features())
        if not features:
            QMessageBox.critical(None, "Error", "No features found in the KML file.")
            return
        
        # Assuming the first feature's geometry is the ROI
        feature = features[0]
        if hasattr(feature, 'geometry'):
            geom = feature.geometry
        elif hasattr(feature, 'features'):
            geom = list(feature.features())[0].geometry
        else:
            QMessageBox.critical(None, "Error", "No geometry found in the KML feature.")
            return
        
        bounds = geom.bounds
        ul_lat, ul_lon = bounds[3], bounds[0]
        lr_lat, lr_lon = bounds[1], bounds[2]
        global roi
        roi = f"{ul_lat},{ul_lon},{lr_lat},{lr_lon}"
        global ROII
        ROII = Polygon([(ul_lon, ul_lat), (lr_lon, ul_lat), (lr_lon, lr_lat), (ul_lon, lr_lat)])
        roiLineEdit.setText(roi)

#%% GENERATE OUTPUT.H5


    
    
def process_files(inDirLineEdit, roiLineEdit, outputFileLineEdit, beamsLineEdit, sdsLineEdit):
    global inDir
    inDir = inDirLineEdit.text()
    roi_input = roiLineEdit.text()
    #output_file = outputFileLineEdit.text()
    output_file = "out.h5"
    beams_input = beamsLineEdit.text()
    sds_input = sdsLineEdit.text()

    if not inDir or not roi_input or not output_file:
        QMessageBox.warning(None, "Input Error", "Please provide all required inputs.")
        return

    roi_coords = roi_input.replace("'", "").split(',')
    
    global ROI
    ROI = [float(r) for r in roi_coords]
    try:
        ROI = Polygon([(ROI[1], ROI[0]), (ROI[3], ROI[0]), (ROI[3], ROI[2]), (ROI[1], ROI[2])]) 
    except:
        QMessageBox.critical(None, "Error", "Unable to read input bounding box coordinates. The required format is: ul_lat,ul_lon,lr_lat,lr_lon.")
        return

    finalClip = gp.GeoDataFrame(index=[0], geometry=[ROI], crs='EPSG:4326')
  
    print(finalClip)

    if inDir[-1] != os.sep:
        inDir = inDir.strip("'").strip('"') + os.sep
    else:
        inDir = inDir

    try:
        os.chdir(inDir)
    except FileNotFoundError:
        QMessageBox.critical(None, "Error", "Input directory provided does not exist or was not found.")
        return
    global beamSubset
    if beams_input:
        beamSubset = beams_input.split(',')
    else:
        beamSubset = ['BEAM0000', 'BEAM0001', 'BEAM0010', 'BEAM0011', 'BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011']
    global layerSubset
    if sds_input:
        layerSubset = sds_input.split(',')
    else:
        layerSubset = None

    parentDir = os.path.dirname(os.path.abspath(inDir))
    outDir = os.path.join(parentDir, 'output_csv') + os.sep

    if not os.path.exists(outDir):
        os.makedirs(outDir)

    gediFiles = [o for o in os.listdir() if o.endswith('.h5') and 'GEDI' in o]

    merged_data = merge_data(gediFiles, beams=beamSubset, sds=layerSubset)

    output_hdf5_file = os.path.join(parentDir, output_file)
    write_to_hdf5(output_hdf5_file, merged_data)
    csv()
    QMessageBox.information(None, "Process Complete", f"Merged HDF5 file created at: {output_hdf5_file}")

def merge_data(files, beams=None, sds=None):
    merged_data = {
        'shot_number': [],
        'IDS': [],
        'rxwaveform': [],
        'lat_lowestmode': [],
        'lon_lowestmode': [],
        'elev_lowestmode': [],
        'rh_a1': [],
        'mean': [],
        'stddev': [],
        'rx_modeamps': [],
        'SNR': [],
        'longitude_bin0': [],
        'latitude_bin0': [],
        'longitude_instrument': [],
        'latitude_instrument': [],
        'altitude_instrument': [],
        'VA': []
        }
    
    if sds:
        for dataset in sds:
            merged_data[dataset] = []

    for file in files:

        print(f"Processing file: {file}")
        print_h5_structure(file)
        file_data = process_file(file, beams, sds)

        for key, values in file_data.items():
            if key == 'rxwaveform':
                if key not in merged_data:
                    merged_data[key] = []
                merged_data[key].extend(values)
        lent = len(merged_data['rxwaveform'])        
        for key, values in file_data.items():
            if key == 'IDS' or key =='SNR' or key =='VA' or key =='longitude_bin0' or key =='latitude_bin0' or key =='longitude_instrument' or key =='latitude_instrument' or key =='altitude_instrument' or key =='shot_number' or key =='lat_lowestmode' or key =='lon_lowestmode' or key =='elev_lowestmode' or key =='rh_a1' or key =='mean' or key =='stddev' or key =='rx_modeamps':
                if key not in merged_data:
                    merged_data[key] = []
                merged_data[key].extend(values[:])
            
        merged_data['shot_number'] = merged_data['shot_number'][:lent]     
        merged_data['IDS'] = merged_data['IDS'][:lent] 
        merged_data['lat_lowestmode'] = merged_data['lat_lowestmode'][:lent] 
        merged_data['lon_lowestmode'] = merged_data['lon_lowestmode'][:lent] 
        merged_data['elev_lowestmode'] = merged_data['elev_lowestmode'][:lent] 
        merged_data['rh_a1'] = merged_data['rh_a1'][:lent] 
        merged_data['mean'] = merged_data['mean'][:lent] 
        merged_data['stddev'] = merged_data['stddev'][:lent] 
        merged_data['rx_modeamps'] = merged_data['rx_modeamps'][:lent] 
        merged_data['SNR'] = merged_data['SNR'][:lent] 
        merged_data['longitude_bin0'] = merged_data['longitude_bin0'][:lent] 
        merged_data['latitude_bin0'] = merged_data['latitude_bin0'][:lent] 
        merged_data['longitude_instrument'] = merged_data['longitude_instrument'][:lent] 
        merged_data['latitude_instrument'] = merged_data['latitude_instrument'][:lent] 
        merged_data['altitude_instrument'] = merged_data['altitude_instrument'][:lent] 
        merged_data['VA'] = merged_data['VA'][:lent] 
        
    return merged_data


def process_file(file_path, beams=None, sds=None):
    with h5py.File(file_path, 'r') as f:
        data = {
            'shot_number': [],
            'IDS': [],
            'rxwaveform': [],
            'lat_lowestmode': [],
            'lon_lowestmode': [],
            'elev_lowestmode': [],
            'rh_a1': [],
            'mean': [],
            'stddev': [],
            'rx_modeamps': [],
            'SNR': [],
            'longitude_bin0': [],
            'latitude_bin0': [],
            'longitude_instrument': [],
            'latitude_instrument': [],
            'altitude_instrument': [],
            'VA': []
            }
        
        if sds:
            for dataset in sds:
                data[dataset] = []

        for beam in [key for key in f.keys() if key.startswith('BEAM')]:
            if beams and beam not in beams:
                continue
            if 'geolocation' not in f[beam]:
                print(f"Skipping {beam} in {file_path}: 'geolocation' group not found.")
                continue
            shot_numbers = f[beam]['geolocation']['shot_number'][:]
            ids = create_ids(shot_numbers)
            data['shot_number'].extend(shot_numbers)
            data['IDS'].extend(ids)
            if 'lon_lowestmode' in f[beam]:
                lon_lm = f[beam]["lon_lowestmode"][:]
                data['lon_lowestmode'].extend(lon_lm)
                
            if 'lat_lowestmode' in f[beam]:
                lat_lm = f[beam]["lat_lowestmode"][:]
                data['lat_lowestmode'].extend(lat_lm)
            
            if 'elev_lowestmode' in f[beam]:
                elev_lm = f[beam]["elev_lowestmode"][:]
                data['elev_lowestmode'].extend(elev_lm)
                
            if 'rh_a1' in f[beam]['geolocation']:
                rh = f[beam]['geolocation']["rh_a1"][:]
                data['rh_a1'].extend(rh)
                
            if 'longitude_bin0' in f[beam]['geolocation']:
                longitude_bin0 = f[beam]['geolocation']["longitude_bin0"][:]
                data['longitude_bin0'].extend(longitude_bin0)
                
            if 'latitude_bin0' in f[beam]['geolocation']:
                latitude_bin0 = f[beam]['geolocation']["latitude_bin0"][:]
                data['latitude_bin0'].extend(latitude_bin0)
                
            if 'longitude_instrument' in f[beam]['geolocation']:
                longitude_instrument = f[beam]['geolocation']["longitude_instrument"][:]
                data['longitude_instrument'].extend(longitude_instrument)
                
            if 'latitude_instrument' in f[beam]['geolocation']:
                latitude_instrument = f[beam]['geolocation']["latitude_instrument"][:]
                data['latitude_instrument'].extend(latitude_instrument)

            if 'altitude_instrument' in f[beam]['geolocation']:
                altitude_instrument = f[beam]['geolocation']["altitude_instrument"][:]
                data['altitude_instrument'].extend(altitude_instrument)                
                
                lon1 = longitude_bin0
                lat1 = latitude_bin0
                lon2 = longitude_instrument
                lat2 = latitude_instrument
                altitude_i =  altitude_instrument
                VA_metric = [VA(lo1,la1,lo2,la2,al) for lo1,la1,lo2,la2,al in zip(lon1,lat1,lon2,lat2,altitude_i)]
                data['VA'].extend(VA_metric)
            
            if 'rx_processing_a1' in f[beam]:
                if 'mean' in f[beam]['rx_processing_a1']:
                    mean = f[beam]['rx_processing_a1']["mean"][:]
                    data['mean'].extend(mean)
                    
                if 'stddev' in f[beam]['rx_processing_a1']:
                    stddev = f[beam]['rx_processing_a1']["stddev"][:]
                    data['stddev'].extend(stddev)
                
                if 'rx_modeamps' in f[beam]['rx_processing_a1']:
                    
                    rx_modeamps = f[beam]['rx_processing_a1']["rx_modeamps"][:]
                    data['rx_modeamps'].extend(rx_modeamps)

                    
                    SNR = calculate_SNR(rx_modeamps,mean,stddev)   #SNR
                    data['SNR'].extend(SNR)
                
       
            
            if sds:
                for dataset in sds:
                    if dataset in f[beam]:
                        data[dataset].extend(f[beam][dataset][:])
                    else:
                        print(f"Dataset {dataset} not found in {beam} of {file_path}")
            if 'rxwaveform' in f[beam]:
                rxwaveform = f[beam]["rxwaveform"][:]
                rx_sample_count = f[beam]["rx_sample_count"][:]
                rx_split_index = f[beam]["rx_sample_start_index"][:]-1
                waveforms = [rxwaveform[x:x+i] for x, i in zip(rx_split_index, rx_sample_count)]
                data["rxwaveform"].extend(waveforms)
            else:
                print(f"rxwaveform dataset not found in {beam} of {file_path}")
               
            
               

    return data

def print_h5_structure(file_path):
    def print_structure(name, obj):
        indent = '  ' * name.count('/')
        print(f"{indent}{name}")
    with h5py.File(file_path, 'r') as f:
        f.visititems(print_structure)

def write_to_hdf5(output_file, data):
    with h5py.File(output_file, 'w') as f:
        df_group = f.create_group('df')
        for key, values in data.items():
            print(f"Writing dataset {key} with {len(values)} items.")
            if key == 'rxwaveform':
                waveform_strings = [','.join(str(value) for value in waveform) for waveform in values]
                dt = h5py.special_dtype(vlen=str)
                df_group.create_dataset(key, data=np.array(waveform_strings, dtype=dt))
            elif isinstance(values[0], str):
                dt = h5py.special_dtype(vlen=str)
                df_group.create_dataset(key, data=np.array(values, dtype=dt))
            else:
                df_group.create_dataset(key, data=np.array(values))

def create_ids(shot_numbers):
    indices = np.arange(len(shot_numbers))
    ids = [f"{shot}_{index}" for shot, index in zip(shot_numbers, indices)]
    return np.array(ids)

def calculate_SNR(rx_modeamps,mean,stddev):
    
    maxamp = rx_modeamps.max(axis=1)
    SNR = [10*math.log10((x-y)/z) if (z>0 and x>y) else 0 for x,y,z in zip(maxamp,mean,stddev)] 
    return SNR
    
### Calculate VA
def haversine(lon1, lat1, lon2, lat2):
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # output distance in meters

def VA(lon1, lat1, lon2, lat2, altitude):
    distance = haversine(lon1, lat1, lon2, lat2)
    return np.rad2deg(math.atan(distance / altitude))

#%% GENERATE CSV    
def csv():
    # --------------------DEFINE PRESET BAND/LAYER SUBSETS ------------------------------------------ #
    # Default layers to be subset and exported, see README for information on how to add additional layers
    l1bSubset = ['/geolocation/latitude_bin0', '/geolocation/longitude_bin0', '/channel', '/shot_number',
                 '/rx_sample_count', '/stale_return_flag', '/tx_sample_count', '/geolocation/altitude_instrument', '/geolocation/latitude_instrument',          
                 '/geolocation/longitude_instrument','/geolocation/degrade', '/geolocation/delta_time', '/geolocation/digital_elevation_model',
                 '/geolocation/solar_elevation',  '/geolocation/local_beam_elevation',  '/noise_mean_corrected',
                 '/geolocation/elevation_bin0', '/geolocation/elevation_lastbin', '/geolocation/surface_type', '/geolocation/digital_elevation_model_srtm']
    l2aSubset = ['/lat_lowestmode', '/lon_lowestmode', '/channel', '/shot_number', '/degrade_flag', '/delta_time', 
                 '/digital_elevation_model', '/elev_lowestmode', '/quality_flag', '/rh', '/sensitivity', '/digital_elevation_model_srtm', 
                 '/elevation_bias_flag', '/surface_flag',  '/num_detectedmodes',  '/selected_algorithm',  '/solar_elevation','/geolocation/elev_lowestmode_a1',
                 '/geolocation/lat_lowestmode_a1', '/geolocation/lon_lowestmode_a1', '/rx_processing_a1/mean', '/geolocation/num_detectedmodes_a1',
    	     '/rx_processing_a1/stddev', '/geolocation/sensitivity_a1', '/rx_processing_a1/zcross0','/rx_processing_a1/botloc','/rx_processing_a1/toploc',
                 '/rx_processing_a1/zcross_amp', '/rx_processing_a1/zcross', '/rx_processing_a1/search_end', '/rx_processing_a1/rx_cumulative','/geolocation/rh_a1']
    l2bSubset = ['/geolocation/lat_lowestmode', '/geolocation/lon_lowestmode', '/channel', '/geolocation/shot_number',
                 '/cover', '/cover_z', '/fhd_normal', '/pai', '/pai_z',  '/rhov',  '/rhog', '/pavd_z', '/l2a_quality_flag', '/l2b_quality_flag', '/rh100', '/sensitivity',
                 '/stale_return_flag', '/surface_flag', '/geolocation/degrade_flag',  '/geolocation/solar_elevation',
                 '/geolocation/delta_time', '/geolocation/digital_elevation_model', '/geolocation/elev_lowestmode','/rx_processing/rx_energy_a1',
                 '/geolocation/latitude_bin0','/geolocation/longitude_bin0']
     
    # -------------------IMPORT GEDI FILES AS GEODATAFRAMES AND CLIP TO ROI-------------------------- #   
    # Loop through each GEDI file and export as a point geojson
    l = 0
    # Create list of GEDI HDF-EOS5 files in the directory
    gediFiles = [o for o in os.listdir() if o.endswith('.h5') and 'GEDI' in o]
    for g in gediFiles:
        l += 1
        print(f"Processing file: {g} ({l}/{len(gediFiles)})")
        gedi = h5py.File(g, 'r')      # Open file
        gediName = g.split('.h5')[0]  # Keep original filename 
        gedi_objs = []            
        gedi.visit(gedi_objs.append)  # Retrieve list of datasets  

        # Search for relevant SDS inside data file
        gediSDS = [str(o) for o in gedi_objs if isinstance(gedi[o], h5py.Dataset)] 
        
        # Define subset of layers based on product
        if 'GEDI01_B' in g:
            sdsSubset = l1bSubset
        elif 'GEDI02_A' in g:
            sdsSubset = l2aSubset 
        else:
            sdsSubset = l2bSubset
        
        # Append additional datasets if provided
        if layerSubset is not None:
            [sdsSubset.append(y) for y in layerSubset]
        
        # Subset to the selected datasets
        gediSDS = [c for c in gediSDS if any(c.endswith(d) for d in sdsSubset)]
            
        # Get unique list of beams and subset to user-defined subset or default (all beams)
        beams = []
        for h in gediSDS:
            beam = h.split('/', 1)[0]
            if beam not in beams and beam in beamSubset:
                beams.append(beam)

        gediDF = pd.DataFrame()  # Create empty dataframe to store GEDI datasets    
        del beam, gedi_objs, h
        
        # Loop through each beam and create a geodataframe with lat/lon for each shot, then clip to ROI
        for b in beams:
            beamSDS = [s for s in gediSDS if b in s]
            
            # Search for latitude, longitude, and shot number SDS
            lat = [l for l in beamSDS if sdsSubset[0] in l][0]  
            lon = [l for l in beamSDS if sdsSubset[1] in l][0]
            shot = f'{b}/shot_number'          
            
            # Open latitude, longitude, and shot number SDS
            shots = gedi[shot][()]
            lats = gedi[lat][()]
            lons = gedi[lon][()]
            
            # Append BEAM, shot number, latitude, longitude and an index to the GEDI dataframe
            geoDF = pd.DataFrame({'BEAM': len(shots) * [b], shot.split('/', 1)[-1].replace('/', '_'): shots,
                                  'Latitude':lats, 'Longitude':lons, 'index': np.arange(0, len(shots), 1)}) 
            
            # Convert lat/lon coordinates to shapely points and append to geodataframe
            geoDF = gp.GeoDataFrame(geoDF, geometry=gp.points_from_xy(geoDF.Longitude, geoDF.Latitude))
            
            # Clip to only include points within the user-defined bounding box
            geoDF = geoDF[geoDF['geometry'].within(ROII.envelope)]    
            gediDF = pd.concat([gediDF, geoDF])
            del geoDF
        
        # Convert to geodataframe and add crs
        gediDF = gp.GeoDataFrame(gediDF)
        gediDF.crs = 'EPSG:4326'
        
        if gediDF.shape[0] == 0:
            print(f"No intersecting shots were found between {g} and the region of interest submitted.")
            continue
        del lats, lons, shots
        
    # --------------------------------OPEN SDS AND APPEND TO GEODATAFRAME---------------------------- #
        beamsDF = pd.DataFrame()  # Create dataframe to store SDS
        j = 0
        
        # Loop through each beam and extract subset of defined SDS
        for b in beams:
            beamDF = pd.DataFrame()
            beamSDS = [s for s in gediSDS if b in s and not any(s.endswith(d) for d in sdsSubset[0:3])]
            shot = f'{b}/shot_number'
            
            try:
                # set up indexes in order to retrieve SDS data only within the clipped subset from above
                mindex = min(gediDF[gediDF['BEAM'] == b]['index'])
                maxdex = max(gediDF[gediDF['BEAM'] == b]['index']) + 1
                shots = gedi[shot][mindex:maxdex]
            except ValueError:
                print(f"No intersecting shots found for {b}")
                continue
            # Loop through and extract each SDS subset and add to DF
            for s in beamSDS:
                j += 1
                sName = s.split('/', 1)[-1].replace('/', '_')

                # Datasets with consistent structure as shots
                if gedi[s].shape == gedi[shot].shape:
                    beamDF[sName] = gedi[s][mindex:maxdex]  # Subset by index
                
                # Datasets with a length of one 
                elif len(gedi[s][()]) == 1:
                    beamDF[sName] = [gedi[s][()][0]] * len(shots) # create array of same single value
                
                # Multidimensional datasets
                elif len(gedi[s].shape) == 2 and 'surface_type' not in s: 
                    allData = gedi[s][()][mindex:maxdex]
                    
                    # For each additional dimension, create a new output column to store those data
                    for i in range(gedi[s].shape[1]):
                        step = []
                        for a in allData:
                            step.append(a[i])
                        beamDF[f"{sName}_{i}"] = step
                
                # Waveforms
                elif s.endswith('waveform') or s.endswith('pgap_theta_z'):
                    waveform = []
                    
                    if s.endswith('waveform'):
                        # Use sample_count and sample_start_index to identify the location of each waveform
                        start = gedi[f'{b}/{s.split("/")[-1][:2]}_sample_start_index'][mindex:maxdex]
                        count = gedi[f'{b}/{s.split("/")[-1][:2]}_sample_count'][mindex:maxdex]
                    
                    # for pgap_theta_z, use rx sample start index and count to subset
                    else:
                        # Use sample_count and sample_start_index to identify the location of each waveform
                        start = gedi[f'{b}/rx_sample_start_index'][mindex:maxdex]
                        count = gedi[f'{b}/rx_sample_count'][mindex:maxdex]
                    wave = gedi[s][()]
                    
                    # in the dataframe, each waveform will be stored as a list of values
                    for k in range(len(start)):
                        singleWF = wave[int(start[k] - 1): int(start[k] - 1 + count[k])]
                        waveform.append(','.join([str(q) for q in singleWF]))
                    beamDF[sName] = waveform
                
                # Surface type 
                elif s.endswith('surface_type'):
                    surfaces = ['land', 'ocean', 'sea_ice', 'land_ice', 'inland_water']
                    allData = gedi[s][()]
                    for i in range(gedi[s].shape[0]):
                        beamDF[f'{surfaces[i]}'] = allData[i][mindex:maxdex]
                    del allData
                else:
                    print(f"SDS: {s} not found")
                print(f"Processing {j} of {len(beamSDS) * len(beams)}: {s}")
            
            beamsDF = pd.concat([beamsDF, beamDF])
        del beamDF, beamSDS, beams, gedi, gediSDS, shots, sdsSubset
        
        # Combine geolocation dataframe with SDS layer dataframe
        outDF = pd.merge(gediDF, beamsDF, left_on='shot_number', right_on=[sn for sn in beamsDF.columns if sn.endswith('shot_number')][0])
        outDF.index = outDF['index']
        del gediDF, beamsDF   
        
        # Keep the exact input geometry for the final clip to ROI
        finalClip = gp.GeoDataFrame(index=[0], geometry=[ROII], crs='EPSG:4326')  
        # Subset the output DF to the actual boundary of the input ROI
        outDF = gp.overlay(outDF, finalClip)
    # --------------------------------EXPORT AS GEOJSON---------------------------------------------- #
        parentDir = os.path.dirname(os.path.abspath(inDir))
        outDir = os.path.join(parentDir, 'output_csv') + os.sep
        # Check for empty output dataframe
        try:

            # Add "IDS" to the csv files
            outDF["IDS"] = outDF["geolocation_shot_number"].astype(str) + "_" + outDF["index"].astype(str)
            
            # Export final geodataframe as csv
            outDF.to_csv(f"{outDir}{g.replace('.h5', '.csv')}", index=False)
            print(f"{g.replace('.h5', '.csv')} saved at: {outDir}")
        except ValueError:
            print(f"{g} intersects the bounding box of the input ROI, but no shots intersect final clipped ROI.")
            
#%% EXTRACT ZIP
def extract_h5_from_zip(file_path, label, progress_bar):
    parent_directory = os.path.dirname(file_path)
    input_folder = os.path.join(parent_directory, 'input')
    os.makedirs(input_folder, exist_ok=True)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        file_count = len([member for member in zip_ref.namelist() if member.lower().endswith('.h5')])
        current_file = 0
        for member in zip_ref.namelist():
            if member.lower().endswith('.h5'):
                current_file += 1
                filename = os.path.basename(member)
                target_path = os.path.join(input_folder, filename)
                with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                label.setText(f"All .h5 files extracted and stored in: {input_folder}")
                progress_bar.setValue(int(current_file / file_count * 100))  # Update progress bar
    progress_bar.setValue(100)  # Ensure progress bar is at 100% after completion




#%% DOWNLOAD DATA 
def open_pdf_file():
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getOpenFileName(None, "Open PDF File", "", "PDF Files (*.pdf)")
    
    if file_path:
        # Assuming manual.pdf is the PDF you want to open in a web browser
        manual_path = os.path.abspath("manual.pdf")
        webbrowser.open_new_tab(f"file://{manual_path}")

            
def open_google_earth():
    
    if platform.system() == "Windows":
        os.system('start "" "C:\\Program Files\\Google\\Google Earth Pro\\client\\googleearth.exe"')
    elif platform.system() == "Darwin":  # macOS
        os.system('open -a "Google Earth Pro"')
    else:  # Assuming Linux
        os.system('google-earth-pro')

def open_gedi_website():
    webbrowser.open('https://search.earthdata.nasa.gov/search')
    
    
#%% OPEN MAP 
def open_map():
    MAP.MAIN()
    
#%% MAIN             
def main():
    app = QApplication(sys.argv)
    main_window = create_main_window()
    
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
