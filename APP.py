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
from PyQt5.QtWidgets import QDialog,QApplication, QMainWindow, QLabel, QVBoxLayout,QGridLayout, QWidget, QLineEdit, QPushButton, QFileDialog, QMessageBox, QTabWidget, QProgressBar,  QPlainTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from fastkml import kml
import platform
import webbrowser
warnings.filterwarnings("ignore")
import subprocess
import glob
import re
import time
from PyQt5.QtCore import Qt, QCoreApplication
# Définir les attributs d'application nécessaires avant la création de QApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFrame,QCheckBox
from PyQt5.QtWebEngineWidgets import QWebEngineView  # Import après Qt.AA_ShareOpenGLContexts
from PyQt5.QtGui import QFont
from threading import Thread
import matplotlib.pyplot as plt 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import folium
from datetime import datetime, timedelta
#%% MAIN WINDOW
# Global variable to hold references to QLineEdit widgets
line_edit_refs = {}

def create_main_window():
    main_window = QMainWindow()
    main_window.setWindowTitle('GEDI VIEWER')
    main_window.setGeometry(400, 200, 1000, 700)

    central_widget = QWidget()
    layout = QVBoxLayout()
    central_widget.setLayout(layout)
    main_window.setCentralWidget(central_widget)

    tab_widget = QTabWidget()

    # Tab for DOWNLOAD
    utilities_tab = QWidget()
    utilities_layout = QVBoxLayout()
    utilities_tab.setLayout(utilities_layout)

    # Layout horizontal pour aligner les boutons côte à côte
    buttons_layout = QHBoxLayout()

    # Bouton pour ouvrir le manuel PDF
    open_pdf_button = QPushButton("📄 Open User Manual")
    open_pdf_button.setFixedSize(300, 500)  # Taille uniforme pour tous les boutons
    open_pdf_button.clicked.connect(open_pp_file)
    open_pdf_button.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    buttons_layout.addWidget(open_pdf_button)

    # Bouton pour ouvrir Google Earth
    open_google_earth_button = QPushButton("🌍 Open Google Earth Pro")
    open_google_earth_button.setFixedSize(300, 500)  # Taille uniforme
    open_google_earth_button.clicked.connect(open_google_earth)
    open_google_earth_button.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    buttons_layout.addWidget(open_google_earth_button)

    # Bouton pour ouvrir la page de téléchargement des données GEDI
    open_gedi_website_button = QPushButton("🌐 Open GEDI Data Download Page")
    open_gedi_website_button.setFixedSize(300, 500)  # Taille uniforme
    open_gedi_website_button.clicked.connect(open_gedi_website)
    open_gedi_website_button.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    buttons_layout.addWidget(open_gedi_website_button)

    # Ajouter les boutons à l'interface
    utilities_layout.addLayout(buttons_layout)

    # Bouton pour fermer l'application
    quit_button = QPushButton("❌ Close")
    quit_button.setFixedSize(300, 50)  # Taille uniforme
    quit_button.clicked.connect(QApplication.instance().quit)
    quit_button.setStyleSheet("""
        QPushButton {
            background: #e74c3c;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #c0392b;
        }
        QPushButton:pressed {
            background: #a93226;
        }
    """)
    utilities_layout.addWidget(quit_button)

    tab_widget.addTab(utilities_tab, "DOWNLOAD")

    # Tab for Drag and Drop Unzipper
    unzip_tab = QWidget()
    unzip_layout = QVBoxLayout()
    unzip_tab.setLayout(unzip_layout)
    
    # Create a frame to hold the drag and drop label
    drag_frame = QFrame()
    drag_frame.setFrameShape(QFrame.Box)
    drag_frame.setFrameShadow(QFrame.Raised)
    drag_frame.setLineWidth(2)
    drag_frame.setStyleSheet("border: 2px dashed #3498db;")
    
    # Layout for the drag frame
    frame_layout = QVBoxLayout()
    drag_frame.setLayout(frame_layout)
    
    # Drag and drop label
    unzip_label = QLabel("Drag and drop zip files here to extract .h5 files:")
    unzip_label.setAlignment(Qt.AlignCenter)
    unzip_label.setFont(QFont('Arial', 12))
    unzip_label.setStyleSheet("font-size: 16px; color: #ecf0f1;")
    
    # Add the label to the frame layout
    frame_layout.addWidget(unzip_label)
    
    # Add the drag frame to the main layout
    unzip_layout.addWidget(drag_frame)
    
    # Drag and drop events
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
    
    # Progress bar
    progress_bar = QProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setValue(0)
    progress_bar.setAlignment(Qt.AlignCenter)
    progress_bar.setStyleSheet("""
        QProgressBar {
            border: none;
            border-radius: 8px;
            background-color: #34495e;
            text-align: center;
            color: #ecf0f1;
        }
        QProgressBar::chunk {
            background-color: #3498db;
            width: 8px;
            margin: 0.5px;
        }
    """)
    unzip_layout.addWidget(progress_bar)
    
    # Quit button
    quit_button = QPushButton("❌ Close")
    quit_button.clicked.connect(QApplication.instance().quit)
    quit_button.setStyleSheet("""
        QPushButton {
            background: #e74c3c;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #c0392b;
        }
        QPushButton:pressed {
            background: #a93226;
        }
    """)
    unzip_layout.addWidget(quit_button)
    
    # Add the tab to the tab widget
    tab_widget.addTab(unzip_tab, "UNZIPPER")
    
    
    
    
    

    # Tab for GEDI DATA GENERATOR
    # Create the main widget and layout
    gen_tab = QWidget()
    gen_layout = QVBoxLayout()
    gen_tab.setLayout(gen_layout)
    
    # Input Directory
    inDirLabel = QLabel("Enter the local directory containing GEDI .h5 files to be processed:")
    inDirLayout = QHBoxLayout()  # Create a new layout for the input directory
    inDirLineEdit = QLineEdit()
    browseDirButton = QPushButton("📁 Browse")
    browseDirButton.clicked.connect(lambda: browse_directory(inDirLineEdit))
    browseDirButton.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    inDirLayout.addWidget(inDirLineEdit)
    inDirLayout.addWidget(browseDirButton)
    
    # KML File Selection
    kmlLabel = QLabel("Select KML file to extract ROI:")
    kmlLayout = QHBoxLayout()  # Create a new layout for the KML selection
    kmlLineEdit = QLineEdit()
    browseKMLButton = QPushButton("📁 Browse")
    browseKMLButton.clicked.connect(lambda: browse_kml(kmlLineEdit))
    browseKMLButton.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    kmlLayout.addWidget(kmlLineEdit)
    kmlLayout.addWidget(browseKMLButton)
    
    # Region of Interest
    roiLabel = QLabel("Region of interest (ROI) extracted:")
    roiLineEdit = QLineEdit()
    roiLineEdit.setReadOnly(True)
    line_edit_refs['roi'] = roiLineEdit 
    
    # Output File
    outputFileLineEdit = "out.h5"
    
    # Beams Input
    # beamsLabel = QLabel("Enter specific beams to be included in the output GeoJSON (optional, default is all beams):")
    # beamsLineEdit = QLineEdit()
    
    # Science Datasets Input
    sdsLabel = QLabel("Enter specific science datasets (SDS) to include in the output .csv file (optional):")
    sdsLineEdit = QLineEdit()
    
    # Algorithm Selection Checkboxes
    algoLabel = QLabel("Select algorithms to be used:")
    algoLayout = QHBoxLayout()  # Create a new layout for the algorithms checkboxes
    algoCheckboxes = []
    algorithms = ["a1", "a2", "a3", "a4", "a5", "a6"]
    for algo in algorithms:
        checkbox = QCheckBox(algo)
        algoLayout.addWidget(checkbox)
        algoCheckboxes.append(checkbox)
    
    # Process Button
    processButton = QPushButton("⚙️ Process Files")
    processButton.clicked.connect(lambda: process_files(inDirLineEdit, roiLineEdit, outputFileLineEdit, sdsLineEdit, algoCheckboxes))
    processButton.setStyleSheet("""
        QPushButton {
            background: #08c993;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #0aa378;
        }
        QPushButton:pressed {
            background: #0a9f6a;
        }
    """)
    
    # Add widgets to the layout
    gen_layout.addWidget(inDirLabel)
    gen_layout.addLayout(inDirLayout)  # Add the input directory layout
    gen_layout.addWidget(kmlLabel)
    gen_layout.addLayout(kmlLayout)  # Add the KML selection layout
    gen_layout.addWidget(roiLabel)
    gen_layout.addWidget(roiLineEdit)
    # gen_layout.addWidget(beamsLabel)
    # gen_layout.addWidget(beamsLineEdit)
    gen_layout.addWidget(sdsLabel)
    gen_layout.addWidget(sdsLineEdit)
    gen_layout.addWidget(algoLabel)
    gen_layout.addLayout(algoLayout)  # Add the algorithms layout
    gen_layout.addWidget(processButton)
    
    # Add the quit button if it exists
    gen_layout.addWidget(quit_button)
    
    # Add the tab to the tab widget and layout
    tab_widget.addTab(gen_tab, "GEDI DATA EXTRACTOR")
    layout.addWidget(tab_widget)
        
    # Tab for GEDI Data Processor
    gedi_tab = QWidget()
    gedi_layout = QVBoxLayout()
    gedi_tab.setLayout(gedi_layout)
    
    outDirLabel = QLabel("Enter the local directory containing CSV files to be merged:")
    outDirLayout = QHBoxLayout()  # Create a new layout for the output directory
    outDirLineEdit = QLineEdit()
    browseoutButton = QPushButton("📁 Browse")
    browseoutButton.clicked.connect(lambda: browse_directory(outDirLineEdit))
    browseoutButton.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    outDirLayout.addWidget(outDirLineEdit)
    outDirLayout.addWidget(browseoutButton)
    
    mergeButton = QPushButton("🔗 Merge CSV")
    mergeButton.clicked.connect(lambda: merge_csv_on_id(outDirLineEdit.text()))
    mergeButton.setStyleSheet("""
        QPushButton {
            background: #08c993;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #0aa378;
        }
        QPushButton:pressed {
            background: #0a9f6a;
        }
    """)
    
    csvLabel = QLabel("Select CSV file to be filtered:")
    csvLayout = QHBoxLayout()  # Create a new layout for the CSV selection
    csvLineEdit = QLineEdit()
    browseCSVButton = QPushButton("📁 Browse")
    browseCSVButton.clicked.connect(lambda: browse_csv(csvLineEdit))
    browseCSVButton.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    csvLayout.addWidget(csvLineEdit)
    csvLayout.addWidget(browseCSVButton)
    
    filterButton = QPushButton("🔍 Filter CSV")
    filterButton.clicked.connect(lambda: filtre(csvLineEdit.text()))
    filterButton.setStyleSheet("""
        QPushButton {
            background: #08c993;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #0aa378;
        }
        QPushButton:pressed {
            background: #0a9f6a;
        }
    """)
    
    csvLabel2 = QLabel("Select CSV file to be split according to algorithms:")
    csvLayout2 = QHBoxLayout()  # Create a new layout for the second CSV selection
    csvLineEdit2 = QLineEdit()
    browseCSVButton2 = QPushButton("📁 Browse")
    browseCSVButton2.clicked.connect(lambda: browse_csv(csvLineEdit2))
    browseCSVButton2.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    csvLayout2.addWidget(csvLineEdit2)
    csvLayout2.addWidget(browseCSVButton2)
    
    splitButton = QPushButton("🔀 Split CSV")
    splitButton.clicked.connect(lambda: split_csv_on_algo(csvLineEdit2.text()))
    splitButton.setProperty('class', 'split-button')
    splitButton.setStyleSheet("""
        QPushButton {
            background: #08c993;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #0aa378;
        }
        QPushButton:pressed {
            background: #0a9f6a;
        }
    """)
    

    gedi_layout.addWidget(outDirLabel)
    gedi_layout.addLayout(outDirLayout)  # Add the output directory layout
    gedi_layout.addWidget(mergeButton)
    gedi_layout.addWidget(csvLabel)
    gedi_layout.addLayout(csvLayout)  # Add the CSV selection layout
    gedi_layout.addWidget(filterButton)
    gedi_layout.addWidget(csvLabel2)
    gedi_layout.addLayout(csvLayout2)  # Add the second CSV selection layout
    gedi_layout.addWidget(splitButton)
    
    quit_button = QPushButton("❌ Close")
    quit_button.clicked.connect(QApplication.instance().quit)
    quit_button.setStyleSheet("""
        QPushButton {
            background: #e74c3c;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #c0392b;
        }
        QPushButton:pressed {
            background: #a93226;
        }
    """)
    gedi_layout.addWidget(quit_button)
    tab_widget.addTab(gedi_tab, "GEDI DATA PROCESSOR")
    
    
    
    
    
    
    # Tab for MAP
    MAP_tab = QWidget()
    MAP_layout = QGridLayout()
    MAP_tab.setLayout(MAP_layout)
    map_button = QPushButton("🗺️ Open Map")
    map_button.setFixedSize(1000, 500)
    
    map_button.clicked.connect(open_map)
    map_button.setStyleSheet("""
        QPushButton {
            background: #3498db;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #2980b9;
        }
        QPushButton:pressed {
            background: #1f618d;
        }
    """)
    MAP_layout.addWidget(map_button)
    quit_button = QPushButton("❌ Close")
    quit_button.clicked.connect(QApplication.instance().quit)
    quit_button.setStyleSheet("""
        QPushButton {
            background: #e74c3c;
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
            border: none;
        }
        QPushButton:hover {
            background: #c0392b;
        }
        QPushButton:pressed {
            background: #a93226;
        }
    """)
    MAP_layout.addWidget(quit_button)
    tab_widget.addTab(MAP_tab, "MAP")
    layout.addWidget(tab_widget)

    # Apply stylesheet
    main_window.setStyleSheet("""
    QWidget {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #2c3e50, stop: 1 #34495e);
        color: #ecf0f1;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    QProgressBar {
        border: none;
        border-radius: 8px;
        background-color: #34495e;
        text-align: center;
        color: #ecf0f1;
    }
    QProgressBar::chunk {
        background-color: #3498db;
        width: 8px;
        margin: 0.5px;
    }
    
    QLabel {
        font-size: 16px;
        color: #ecf0f1;
    }
    
    QLineEdit {
        padding: 8px;
        font-size: 16px;
        border-radius: 8px;
        border: 1px solid #3498db;
        background-color: #2c3e50;
        color: #ecf0f1;
    }
    
    QTabWidget::pane {
        border: none;
    }
    
    QTabBar::tab {
        background-color: #34495e;
        color: #bdc3c7;
        padding: 10px;
        border: none;
        border-bottom: 2px solid #2c3e50;
    }
    QTabBar::tab:selected {
        background-color: #2c3e50;
        color: #ecf0f1;
    }
    QTabBar::tab:hover {
        background-color: #3b4b5b;
    }
    """)

    return main_window


#%% DOWNLOAD DATA 
def open_pp_file():
    # Obtient le chemin absolu du répertoire où se trouve le script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construit le chemin complet vers MANUAL.pptx
    file_path = os.path.join(script_dir, "MANUAL.pptx")
    
    # Vérifie si le fichier existe
    if os.path.exists(file_path):
        # Ouvre le fichier PPTX dans PowerPoint
        os.startfile(file_path)
    else:
        print("Le fichier MANUAL.pptx n'existe pas dans le répertoire du script.")

            
def open_google_earth():
    
    if platform.system() == "Windows":
        os.system('start "" "C:\\Program Files\\Google\\Google Earth Pro\\client\\googleearth.exe"')
    elif platform.system() == "Darwin":  # macOS
        os.system('open -a "Google Earth Pro"')
    else:  # Assuming Linux
        os.system('google-earth-pro')

def open_gedi_website():
    webbrowser.open('https://search.earthdata.nasa.gov/search')
    
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
        
def browse_csv(csvLineEdit):
    file_name, _ = QFileDialog.getOpenFileName(None, "Select CSV File", "", "CSV files (*.csv)")
    if file_name:
        csvLineEdit.setText(file_name)
        

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
def process_files(inDirLineEdit, roiLineEdit, outputFileLineEdit, sdsLineEdit, algoCheckboxes):
    

    selected_algorithms = []
    exclusion_algo = ["a1", "a2", "a3", "a4", "a5", "a6"]
    for checkbox in algoCheckboxes:
        if checkbox.isChecked():
            selected_algorithms.append(checkbox.text())
            exclusion_algo.remove(checkbox.text()) 
    

    
    

    global inDir
    inDir = inDirLineEdit.text()
    roi_input = roiLineEdit.text()
    #output_file = outputFileLineEdit.text()
    output_file = "out.h5"
    beams_input = None
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
  
    # print(finalClip)

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
    # Création de la boîte de dialogue avec une barre de chargement
    progress_dialog = QDialog()
    progress_dialog.setWindowTitle("Processing Files")
    layout = QVBoxLayout(progress_dialog)
    progress_bar = QProgressBar()
    layout.addWidget(progress_bar)
    progress_dialog.setLayout(layout)
    progress_dialog.show()
    # Traitement des fichiers avec une barre de chargement
    total_files = len(gediFiles)
    progress_bar.setMaximum(total_files)
    
    for i, file in enumerate(gediFiles):
        # Votre fonction de fusion des données ici
        merged_data = merge_data([file], beams=beamSubset, sds=layerSubset)
        
        # Mise à jour de la barre de chargement
        progress_bar.setValue(i + 1)
        QApplication.processEvents()  # Assurez-vous que la barre de chargement se met à jour


    merged_data = merge_data(gediFiles, beams=beamSubset, sds=layerSubset)

    output_hdf5_file = os.path.join(parentDir, output_file)
    write_to_hdf5(output_hdf5_file, merged_data)
    csv(exclusion_algo)
    progress_dialog.close()


    QMessageBox.information(None, "Process Completed", f"Merged HDF5 file created at: {output_hdf5_file}")

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
        'VA': [],
        'digital_elevation_model_srtm': [],
        'num_detectedmodes_a1': [],
        'elev_lowestmode_a1': [],
        'rx_sample_count': [],
        'search_end': []
        }
    
    if sds:
        for dataset in sds:
            merged_data[dataset] = []

    for file in files:

        # print(f"Processing file: {file}")
        # print_h5_structure(file)
        file_data = process_file(file, beams, sds)

        # for key, values in file_data.items():
        #     if key == 'rxwaveform':
        #         if key not in merged_data:
        #             merged_data[key] = []
        #         merged_data[key].extend(values)
        # lent = len(merged_data['rxwaveform'])        
        for key, values in file_data.items():
           
            if key not in merged_data:
                merged_data[key] = []
            merged_data[key].extend(values[:])
          
        
       
        
        merged_data['rxwaveform'] = merged_data['rxwaveform'][:]    
        lent = len(merged_data['rxwaveform'])

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
        merged_data['num_detectedmodes_a1'] = merged_data['num_detectedmodes_a1'][:lent] 
        merged_data['elev_lowestmode_a1'] = merged_data['elev_lowestmode_a1'][:lent] 
        merged_data['rx_sample_count'] = merged_data['rx_sample_count'][:lent] 
        merged_data['search_end'] = merged_data['search_end'][:lent] 
        merged_data['digital_elevation_model_srtm'] = merged_data['digital_elevation_model_srtm'][:lent] 
   
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
            'VA': [],
            'digital_elevation_model_srtm': [],
            'num_detectedmodes_a1': [],
            'elev_lowestmode_a1': [],
            'rx_sample_count': [],
            'search_end': []
            }
        
        if sds:
            for dataset in sds:
                data[dataset] = []

        for beam in [key for key in f.keys() if key.startswith('BEAM')]:
            if beams and beam not in beams:
                continue
            if 'geolocation' not in f[beam]:
                # print(f"Skipping {beam} in {file_path}: 'geolocation' group not found.")
                continue
            shot_numbers = f[beam]['geolocation']['shot_number'][:]
            ids = create_ids(shot_numbers)
            data['shot_number'].extend(shot_numbers)
            data['IDS'].extend(ids)
            
            if 'digital_elevation_model_srtm' in f[beam]:
                z = f[beam]['digital_elevation_model_srtm'][:]
                data['digital_elevation_model_srtm'].extend(z)       
            if 'rx_sample_count' in f[beam]:
                z = f[beam]['rx_sample_count'][:]
                data['rx_sample_count'].extend(z) 
                
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
                
                if 'search_end' in f[beam]['rx_processing_a1']:
                    z = f[beam]['rx_processing_a1']['search_end'][:]
                    data['search_end'].extend(z) 
                    
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
                
                
            if 'geolocation' in f[beam]:
               if 'num_detectedmodes_a1' in f[beam]['geolocation']:
                   a = f[beam]['geolocation']['num_detectedmodes_a1'][:]
                   data['num_detectedmodes_a1'].extend(a) 
               if 'elev_lowestmode_a1' in f[beam]['geolocation']:
                   z = f[beam]['geolocation']['elev_lowestmode_a1'][:]
                   data['elev_lowestmode_a1'].extend(z) 
                       
                
            if sds:
                for dataset in sds:
                    if dataset in f[beam]:
                        data[dataset].extend(f[beam][dataset][:])
                    # else:
                    #     # print(f"Dataset {dataset} not found in {beam} of {file_path}")
            if 'rxwaveform' in f[beam]:
                rxwaveform = f[beam]["rxwaveform"][:]
                rx_sample_count = f[beam]["rx_sample_count"][:]
                rx_split_index = f[beam]["rx_sample_start_index"][:]-1
                waveforms = [rxwaveform[x:x+i] for x, i in zip(rx_split_index, rx_sample_count)]
                data["rxwaveform"].extend(waveforms)
            # else:
            #     print(f"rxwaveform dataset not found in {beam} of {file_path}")
               
            
               

    return data

def print_h5_structure(file_path):
    def print_structure(name, obj):
        indent = '  ' * name.count('/')
        # print(f"{indent}{name}")
    with h5py.File(file_path, 'r') as f:
        f.visititems(print_structure)

def write_to_hdf5(output_file, data):
    with h5py.File(output_file, 'w') as f:
        df_group = f.create_group('df')
        for key, values in data.items():
            # print(f"Writing dataset {key} with {len(values)} items.")

            if key == 'rxwaveform' :
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

def show_progress_message(num_files_processed, total_files):
    """Affiche une boîte de dialogue indiquant la progression en utilisant PyQt."""
    app = QApplication([])  # Crée une application PyQt (nécessaire pour les dialogues)
    
    # Crée une boîte de message pour afficher la progression
    message = f"Fichiers générés : {num_files_processed}/{total_files}"
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setText(message)
    msgBox.setWindowTitle("Progression")
    msgBox.exec_()    
    
def csv(exclusion_algo):
    
        
        
    # --------------------DEFINE PRESET BAND/LAYER SUBSETS ------------------------------------------ #
    # Default layers to be subset and exported, see README for information on how to add additional layers
    l1bSubset = ['/geolocation/latitude_bin0', '/geolocation/longitude_bin0', '/channel', '/shot_number',
                 '/rx_sample_count', '/stale_return_flag', '/tx_sample_count', '/geolocation/altitude_instrument', '/geolocation/latitude_instrument',          
                 '/geolocation/longitude_instrument','/geolocation/degrade', '/geolocation/delta_time', '/geolocation/digital_elevation_model',
                 '/geolocation/solar_elevation',  '/geolocation/local_beam_elevation',  '/noise_mean_corrected',
                 '/geolocation/elevation_bin0', '/geolocation/elevation_lastbin', '/geolocation/surface_type', '/geolocation/digital_elevation_model_srtm']
    l2aSubset = [
    '/lat_lowestmode', '/lon_lowestmode', '/channel', '/shot_number', '/degrade_flag', '/delta_time',
    '/digital_elevation_model', '/elev_lowestmode', '/quality_flag', '/rh', '/sensitivity', '/digital_elevation_model_srtm',
    '/elevation_bias_flag', '/surface_flag', '/num_detectedmodes', '/selected_algorithm', '/solar_elevation',
    '/geolocation/elev_lowestmode_a1', '/geolocation/lat_lowestmode_a1', '/geolocation/lon_lowestmode_a1','/rx_processing_a1/rx_modeamps',
    '/rx_processing_a1/mean', '/geolocation/num_detectedmodes_a1', '/rx_processing_a1/stddev',
    '/geolocation/sensitivity_a1', '/rx_processing_a1/zcross0', '/rx_processing_a1/botloc', '/rx_processing_a1/toploc',
    '/rx_processing_a1/zcross_amp', '/rx_processing_a1/zcross', '/rx_processing_a1/search_end', '/rx_processing_a1/rx_cumulative',
    '/geolocation/rh_a1',
    '/geolocation/elev_lowestmode_a2', '/geolocation/lat_lowestmode_a2', '/geolocation/lon_lowestmode_a2',
    '/rx_processing_a2/mean', '/geolocation/num_detectedmodes_a2', '/rx_processing_a2/stddev',
    '/geolocation/sensitivity_a2', '/rx_processing_a2/zcross0', '/rx_processing_a2/botloc', '/rx_processing_a2/toploc',
    '/rx_processing_a2/zcross_amp', '/rx_processing_a2/zcross', '/rx_processing_a2/search_end', '/rx_processing_a2/rx_cumulative',
    '/geolocation/rh_a2',
    '/geolocation/elev_lowestmode_a3', '/geolocation/lat_lowestmode_a3', '/geolocation/lon_lowestmode_a3',
    '/rx_processing_a3/mean', '/geolocation/num_detectedmodes_a3', '/rx_processing_a3/stddev',
    '/geolocation/sensitivity_a3', '/rx_processing_a3/zcross0', '/rx_processing_a3/botloc', '/rx_processing_a3/toploc',
    '/rx_processing_a3/zcross_amp', '/rx_processing_a3/zcross', '/rx_processing_a3/search_end', '/rx_processing_a3/rx_cumulative',
    '/geolocation/rh_a3',
    '/geolocation/elev_lowestmode_a4', '/geolocation/lat_lowestmode_a4', '/geolocation/lon_lowestmode_a4',
    '/rx_processing_a4/mean', '/geolocation/num_detectedmodes_a4', '/rx_processing_a4/stddev',
    '/geolocation/sensitivity_a4', '/rx_processing_a4/zcross0', '/rx_processing_a4/botloc', '/rx_processing_a4/toploc',
    '/rx_processing_a4/zcross_amp', '/rx_processing_a4/zcross', '/rx_processing_a4/search_end', '/rx_processing_a4/rx_cumulative',
    '/geolocation/rh_a4',
    '/geolocation/elev_lowestmode_a5', '/geolocation/lat_lowestmode_a5', '/geolocation/lon_lowestmode_a5',
    '/rx_processing_a5/mean', '/geolocation/num_detectedmodes_a5', '/rx_processing_a5/stddev',
    '/geolocation/sensitivity_a5', '/rx_processing_a5/zcross0', '/rx_processing_a5/botloc', '/rx_processing_a5/toploc',
    '/rx_processing_a5/zcross_amp', '/rx_processing_a5/zcross', '/rx_processing_a5/search_end', '/rx_processing_a5/rx_cumulative',
    '/geolocation/rh_a5',
    '/geolocation/elev_lowestmode_a6', '/geolocation/lat_lowestmode_a6', '/geolocation/lon_lowestmode_a6',
    '/rx_processing_a6/mean', '/geolocation/num_detectedmodes_a6', '/rx_processing_a6/stddev',
    '/geolocation/sensitivity_a6', '/rx_processing_a6/zcross0', '/rx_processing_a6/botloc', '/rx_processing_a6/toploc',
    '/rx_processing_a6/zcross_amp', '/rx_processing_a6/zcross', '/rx_processing_a6/search_end', '/rx_processing_a6/rx_cumulative',
    '/geolocation/rh_a6'
    ]

    l2bSubset = [
    '/geolocation/lat_lowestmode', '/geolocation/lon_lowestmode', '/channel', '/geolocation/shot_number',
    '/cover', '/cover_z', '/fhd_normal', '/pai', '/pai_z', '/rhov', '/rhog', '/pavd_z', '/l2a_quality_flag', 
    '/l2b_quality_flag', '/rh100', '/sensitivity', '/stale_return_flag', '/surface_flag', '/geolocation/degrade_flag',
    '/geolocation/solar_elevation', '/geolocation/delta_time', '/geolocation/digital_elevation_model', 
    '/geolocation/elev_lowestmode', '/rx_processing/rx_energy_a1',
    '/geolocation/latitude_bin0', '/geolocation/longitude_bin0',
    '/geolocation/lat_lowestmode_a2', '/geolocation/lon_lowestmode_a2', '/geolocation/shot_number_a2',
    '/rx_processing/rx_energy_a2', '/geolocation/latitude_bin0_a2', '/geolocation/longitude_bin0_a2',
    '/geolocation/lat_lowestmode_a3', '/geolocation/lon_lowestmode_a3', '/geolocation/shot_number_a3',
    '/rx_processing/rx_energy_a3', '/geolocation/latitude_bin0_a3', '/geolocation/longitude_bin0_a3',
    '/geolocation/lat_lowestmode_a4', '/geolocation/lon_lowestmode_a4', '/geolocation/shot_number_a4',
    '/rx_processing/rx_energy_a4', '/geolocation/latitude_bin0_a4', '/geolocation/longitude_bin0_a4',
    '/geolocation/lat_lowestmode_a5', '/geolocation/lon_lowestmode_a5', '/geolocation/shot_number_a5',
    '/rx_processing/rx_energy_a5', '/geolocation/latitude_bin0_a5', '/geolocation/longitude_bin0_a5',
    '/geolocation/lat_lowestmode_a6', '/geolocation/lon_lowestmode_a6', '/geolocation/shot_number_a6',
    '/rx_processing/rx_energy_a6', '/geolocation/latitude_bin0_a6', '/geolocation/longitude_bin0_a6'
    ]   
     
    
    # --------------------------------------FILTER--------------------------------------------- #  
    for i in range(len(exclusion_algo)) : 
        l1bSubset = [ j for j in l1bSubset if exclusion_algo[i] not in j ]
        l2aSubset = [ j for j in l2aSubset if exclusion_algo[i] not in j ]
        l2bSubset = [ j for j in l2bSubset if exclusion_algo[i] not in j ]
        
        
        
    
                      
    # ----------------------------------------------------------------------------------------- # 
    
    
    
    
    
    
    # -------------------IMPORT GEDI FILES AS GEODATAFRAMES AND CLIP TO ROI-------------------------- #   
    # Loop through each GEDI file and export as a point geojson
    l = 0
    # Create list of GEDI HDF-EOS5 files in the directory
    gediFiles = [o for o in os.listdir() if o.endswith('.h5') and 'GEDI' in o]
    total_files = len(gediFiles)  # Nombre total de fichiers à traiter
    
    # Import GEDI files and set up PyQt application
    bar = QApplication([])
    
    # Create a main window and set up a progress bar
    window = QMainWindow()
    window.setWindowTitle("Progress")
    window.setGeometry(100, 100, 300, 100)  # (x, y, width, height)
    
    progress_dialog = QDialog()
    progress_dialog.setWindowTitle("Processing Files")
    layout = QVBoxLayout(progress_dialog)
    
    progress_bar = QProgressBar()
    layout.addWidget(progress_bar)
    progress_label = QLabel()
    layout.addWidget(progress_label)
    layout.addWidget(progress_bar)
    progress_dialog.show()
    progress_bar.setMaximum(total_files)
  
    for g in gediFiles:
        l += 1
        # print(f"Processing file: {g} ({l}/{len(gediFiles)})")
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
            # print(f"No intersecting shots were found between {g} and the region of interest submitted.")
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
                # print(f"No intersecting shots found for {b}")
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
                # else:
                #     print(f"SDS: {s} not found")
                # print(f"Processing {j} of {len(beamSDS) * len(beams)}: {s}")
            
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
            # print(f"{g.replace('.h5', '.csv')} saved at: {outDir}")
        except ValueError:
            print(f"{g} intersects the bounding box of the input ROI, but no shots intersect final clipped ROI.")
        # Update progress bar
        progress_bar.setValue(l)
        progress_label.setText(f".csv files generated : {l}/{total_files}")
        QApplication.processEvents()  # Permet à l'interface de se mettre à jour
   
    
# Merge all CSV et ajout de VA et SNR
def merge_csv_on_id(output_dir):
    parentDir = os.path.dirname(os.path.abspath(output_dir))
    
    # Liste de tous les fichiers CSV dans le répertoire de sortie
    csv_files = glob.glob(os.path.join(output_dir, '*.csv'))
    
    # Création de la boîte de dialogue avec une barre de chargement et un label
    progress_dialog = QDialog()
    progress_dialog.setWindowTitle("Processing Files")
    layout = QVBoxLayout(progress_dialog)
    progress_bar = QProgressBar()
    label = QLabel("Starting process...")
    layout.addWidget(label)
    layout.addWidget(progress_bar)
    progress_dialog.setLayout(layout)
    progress_dialog.show()

    # Initialisation du DataFrame final
    final_df = pd.DataFrame()

    total_files = len(csv_files)
    progress_bar.setMaximum(total_files)
    
    for i, csv_file in enumerate(csv_files):
        # Mise à jour de la barre de chargement
        progress_bar.setValue(i + 1)
        label.setText(f"Processing file {i + 1} of {total_files}: {os.path.basename(csv_file)}")
        QApplication.processEvents()  # Assurez-vous que l'UI se met à jour
        
        # Lecture du CSV
        df = pd.read_csv(csv_file)
        
        # Fusion avec le DataFrame final basé sur la colonne 'IDS'
        if final_df.empty:
            final_df = df
        else:
            final_df = pd.merge(final_df, df, on='IDS', how='outer', suffixes=('', '_new'))
            for column in df.columns:
                if column != 'IDS' and f'{column}_new' in final_df.columns:
                    final_df[column].fillna(final_df[f'{column}_new'], inplace=True)
                    final_df.drop(columns=[f'{column}_new'], inplace=True)
                    
    # Récupération des colonnes nécessaires
    if all(col in final_df.columns for col in [
        'rx_processing_a1_mean', 'rx_processing_a1_stddev', 'rx_processing_a1_rx_modeamps_0',
        'geolocation_longitude_bin0', 'geolocation_latitude_bin0',
        'geolocation_longitude_instrument', 'geolocation_latitude_instrument',
        'geolocation_altitude_instrument']):
        
        mean = final_df['rx_processing_a1_mean']
        stddev = final_df['rx_processing_a1_stddev']
        lon1 = final_df['geolocation_longitude_bin0']
        lat1 = final_df['geolocation_latitude_bin0']
        lon2 = final_df['geolocation_longitude_instrument']
        lat2 = final_df['geolocation_latitude_instrument']
        altitude_i = final_df['geolocation_altitude_instrument']
        
        
        # Extraction des colonnes rx_modeamps
        amp_columns = [col for col in final_df.columns if col.startswith('rx_processing_a1_rx_modeamps_')]
        maxamp = final_df[amp_columns].max(axis=1)
        
        # Calcul du SNR
        final_df['SNR'] = [10*math.log10((x-y)/z) if (z > 0 and x > y) else 0 for x, y, z in zip(maxamp, mean, stddev)]
        
        # Calcul du VA
        VA_metric = [VA(lo1, la1, lo2, la2, al) for lo1, la1, lo2, la2, al in zip(lon1, lat1, lon2, lat2, altitude_i)]
        final_df['VA'] = VA_metric
        
        # Calcul du Datetime
        final_df['DateTime'] = final_df['delta_time'].apply(lambda x: (datetime(2018, 1, 1, 0, 0, 0) + timedelta(seconds=x)) if not pd.isna(x) else pd.NaT)
    else :
        print("non")
    # Réorganiser les colonnes pour placer 'IDS' en premier
    if 'IDS' and 'SNR' and 'VA' in final_df.columns:
        cols = ['IDS'] + ['SNR'] + ['VA'] + ['DateTime'] + [col for col in final_df.columns if col != 'IDS' and col != 'SNR' and col != 'VA' and col != 'DateTime']
        final_df = final_df[cols]
        
    # Enregistrement du DataFrame fusionné
    final_output_path = os.path.join(parentDir, 'merged_output.csv')

    final_df.to_csv(final_output_path, index=False, sep=';', encoding='utf-8-sig')
    # final_df.to_csv(final_output_path, index=False)
    # Mise à jour finale de la barre de progression et du label
    progress_bar.setValue(total_files)
    label.setText(f"Process completed. File saved to: {final_output_path}")
    
    # Lire le fichier CSV pour obtenir le nombre de lignes et de colonnes
    merged_df = pd.read_csv(final_output_path, sep=';', encoding='utf-8-sig')
    num_rows, num_cols = merged_df.shape

    # Fermeture de la boîte de dialogue après un court délai
    QApplication.processEvents()
    progress_dialog.close()
    
    # Message de confirmation
    QMessageBox.information(None, "Process Completed", f"Merged CSV file created at: {final_output_path}\nNumber of rows: {num_rows}\nNumber of columns: {num_cols}")

 
# filter CSV file according to SNR
def filtre(csvLineEdit):
    
    csvLineEdit = csvLineEdit.replace("/", "\\")
    csvLineEdit = f'{csvLineEdit}'
    parentDir = os.path.dirname(os.path.abspath(csvLineEdit))
    # Lire le fichier CSV dans un DataFrame
    df = pd.read_csv(csvLineEdit, delimiter=';')
    init_len = len(df['IDS'])
    
    df = df[df['SNR'] != 0]
    df = df[df['geolocation_num_detectedmodes_a1'] != 0]
    df= df[abs(df['digital_elevation_model_srtm'] - df['geolocation_elev_lowestmode_a1']) < 100]
    df= df[(df['rx_sample_count'] - df['rx_processing_a1_search_end']) > 0]
    final_len = len(df['IDS'])
    
    lenght = init_len - final_len 

    # Enregistrement du DataFrame fusionné
    final_output_path = os.path.join(parentDir, 'merged_output.csv')
    df.to_csv(final_output_path, index=False, sep=';', encoding='utf-8-sig')
    # Message de confirmation
    
    #FILTER .h5
    h5_file_path = os.path.join(parentDir, "out.h5")
    with h5py.File(h5_file_path, 'r+') as h5file:
            # Extraction des datasets
            ids = np.array(h5file['df']['IDS'])
            snr = np.array(h5file['df']['SNR'])
            geolocation_num_detectedmodes_a1 = np.array(h5file['df']['num_detectedmodes_a1'])
            dem_srtm = np.array(h5file['df']['digital_elevation_model_srtm'])
            elev_lowestmode_a1 = np.array(h5file['df']['elev_lowestmode_a1'])
            rx_sample_count = np.array(h5file['df']['rx_sample_count'])
            rx_processing_a1_search_end = np.array(h5file['df']['search_end'])
            rx_waveform = np.array(h5file['df']['rxwaveform'])

            # Indices à conserver
            indices_to_keep = np.where(
                (snr != 0) &
                (geolocation_num_detectedmodes_a1 != 0) &
                (abs(dem_srtm - elev_lowestmode_a1) < 100) &
                ((rx_sample_count[:len(rx_sample_count)-1] - rx_processing_a1_search_end) > 0)
            )[0]

            df_group = h5file['df']
            # Filtrage et suppression des anciens datasets
            for dataset_name in df_group.keys():
                dataset = np.array(df_group[dataset_name])
                filtered_dataset = dataset[indices_to_keep]
                
                # Suppression de l'ancien dataset
                del df_group[dataset_name]
                # Ajout du dataset filtré
                df_group.create_dataset(dataset_name, data=filtered_dataset)
                
    # Lire le fichier CSV pour obtenir le nombre de lignes et de colonnes
    merged_df = pd.read_csv(final_output_path, sep=';', encoding='utf-8-sig')
    num_rows, num_cols = merged_df.shape

    QMessageBox.information(None, "Process Completed", f"File filtered \n Number of data filtered : {lenght}\nNumber of rows: {num_rows}\nNumber of columns: {num_cols}")


def split_csv_on_algo(csvLineEdit):
    csvLineEdit = csvLineEdit.replace("/", "\\")
    csvLineEdit = f'{csvLineEdit}'
    parentDir = os.path.dirname(os.path.abspath(csvLineEdit))
    
    # Lire le fichier CSV dans un DataFrame
    df = pd.read_csv(csvLineEdit, delimiter=';')
    
    test = ['geolocation_lon_lowestmode_a1','geolocation_lon_lowestmode_a2','geolocation_lon_lowestmode_a3',
            'geolocation_lon_lowestmode_a4','geolocation_lon_lowestmode_a5','geolocation_lon_lowestmode_a6']
    
    
    selected = []
    keywords = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6']
    for i in range(len(test)) : 
            
        if test[i] in df.columns:
            selected.append(keywords[i])
        

   
    
    for keyword in keywords:
        if keyword in selected : 
            # Construire le motif d'exclusion pour le fichier courant
            exclusion_keywords = [kw for kw in keywords if kw != keyword]
            pattern = '|'.join([re.escape(kw) for kw in exclusion_keywords])
            
            # Sélectionner les colonnes qui ne contiennent pas les mots-clés d'exclusion
            selected_columns = [col for col in df.columns if not re.search(pattern, col)]
            
            # Extraire les données filtrées
            df_filtered = df[selected_columns]
            
            # Créer un dossier pour chaque algorithme (a1, a2, ...)
            algo_folder = os.path.join(parentDir, keyword)
            os.makedirs(algo_folder, exist_ok=True)
            
            
            # Diviser en paquets 
            TAILLE_MAX = 10**5
            num_chunks = (len(df_filtered) // TAILLE_MAX) + 1
            
            for chunk_number in range(num_chunks):
                start_row = chunk_number * TAILLE_MAX
                end_row = (chunk_number + 1) * TAILLE_MAX
                
                # Extraire le sous-ensemble de données
                df_chunk = df_filtered[start_row:end_row]
                
                # Déterminer le nom du fichier de sortie avec suffixe _1, _2, etc.
                output_file = os.path.join(algo_folder, f"{keyword}_{chunk_number + 1}.csv")
                df_chunk.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
                # print(f"Fichier {output_file} créé avec succès.")
            
    selected = ' // '.join(selected)    

    # Message de confirmation
    QMessageBox.information(None, f"Process Completed", f"File splited into algo : {selected}  ")
   
#%% OPEN MAP 
def open_map():
    MAP.MAIN()
    
#%% MAIN             
def main():
    app = QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    
    file_PATH = os.path.join(script_dir, "icone.ico")
    app.setWindowIcon(QIcon(file_PATH))
    main_window = create_main_window()
    main_window.setWindowIcon(QIcon(file_PATH))
    
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
