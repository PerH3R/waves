from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QFormLayout, QTabWidget, QFileDialog, QCheckBox, QLabel, QLineEdit
from os import getcwd

from tileGenerator import tileGen
from tileNeighbourDetector import tileNBdetect
from wavecollapser_placeholder import waveCollapse

# Create the app's main window
class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Title
        self.setWindowTitle("Waves")

        # Window size
        self.left = 0
        self.top = 0
        self.width = 600
        self.height = 400
        self.setMinimumSize(self.width, self.height)

        # Set widget with tabs
        self.table_widget = Tabs(self)
        self.setCentralWidget(self.table_widget)
        
        self.show()


class Tabs(QWidget):
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QFormLayout(self)
        
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        # self.tabs.resize(400,300)
        
        # Add tabs
        self.tabs.addTab(self.tab1,"Tileset extraction")
        self.tabs.addTab(self.tab2,"Tileset rule generator")
        self.tabs.addTab(self.tab3,"Wave collapser")
        
        # Create Tab 1: Extracting the tileset
        self.tab1_layout = QFormLayout(self.tab1)
        self.inputfilename = QLineEdit()
        self.tab1_layout.addRow(self.tr("Input tileset filename:"), self.inputfilename)    

        self.pushButton1 = QPushButton("Select tileset")
        self.pushButton1.clicked.connect(lambda: self.Browser(file_filter="Image file (*.png *.bmp *.tiff *.jpg *.jpeg)", button_caption="Open Tileset", input_field=self.inputfilename))
        self.tab1_layout.addWidget(self.pushButton1)


        self.tileoutputfolder = QLineEdit()
        self.tab1_layout.addRow(self.tr("Output tileset folder:"), self.tileoutputfolder)    

        self.pushButton1o = QPushButton("Select output folder")
        self.pushButton1o.clicked.connect(lambda: self.Browser(file_filter="dir", button_caption="Extract to folder", input_field=self.tileoutputfolder))
        self.tab1_layout.addWidget(self.pushButton1o)

        # Toggle for autodetecting the grid of the tileset
        self.toggleAutoDetect = QCheckBox("Autodetect Tile- and Gridsize")
        self.toggleAutoDetect.clicked.connect(self.autoDetectToggle)
        self.tab1_layout.addWidget(self.toggleAutoDetect)
        self.toggleAutoDetect.setChecked(True)
        
        # For manual parameters for grid detection
        # Tilesize
        self.tileSize = QLineEdit()
        self.tab1_layout.addRow(self.tr("Tilesize (x and y) in px:"), self.tileSize)
        # Grid offset
        self.gridOffsetX = QLineEdit()
        self.tab1_layout.addRow(self.tr("Grid offset X in px:"), self.gridOffsetX)
        # Grid offset Y
        self.gridOffsetY = QLineEdit()
        self.tab1_layout.addRow(self.tr("Grid offset Y in px:"), self.gridOffsetY)
        # Grid width
        self.gridSize = QLineEdit()
        self.tab1_layout.addRow(self.tr("Grid width in px:"), self.gridSize)
        
        self.autoDetectToggle()

        # Set tilesizepx to correct value, and to None if no value is filled in.
        tileSize = int(self.tileSize.text()) if len(self.tileSize.text()) > 0 else None
        gridOffsetXpx = int(self.gridOffsetX.text()) if len(self.gridOffsetX.text()) > 0 else None
        gridOffsetYpx = int(self.gridOffsetY.text()) if len(self.gridOffsetY.text()) > 0 else None
        gridSize = int(self.gridSize.text()) if len(self.gridSize.text()) > 0 else None

        # Execute button
        self.pushButtonGo1 = QPushButton("Extract tiles from tileset")
        
        self.pushButtonGo1.clicked.connect(lambda: tileGen(filename_path=self.inputfilename.text(), output_path=self.tileoutputfolder.text() , tile_size=tileSize, grid_offset_x=gridOffsetXpx, grid_offset_y=gridOffsetYpx, grid_size=gridSize))
        self.tab1_layout.addWidget(self.pushButtonGo1)
        self.tab1.setLayout(self.tab1_layout)


        # Create Tab 2: determining the rules of the world by matching tileset in world
        self.tab2_layout = QFormLayout(self.tab2)

        # Selecting tileset folder
        self.tilesetfolder = QLineEdit()
        self.tab2_layout.addRow(self.tr("Input tileset folder:"), self.tilesetfolder)    

        self.pushButton2 = QPushButton("Select tileset folder")
        self.pushButton2.clicked.connect(lambda: self.Browser(file_filter="dir", button_caption="Open Tileset Folder", input_field=self.tilesetfolder))
        self.tab2_layout.addWidget(self.pushButton2)

        # Selecting world image
        self.inputworld = QLineEdit()
        self.tab2_layout.addRow(self.tr("Overworld image filename:"), self.inputworld)    

        self.pushButton3 = QPushButton("Select world")
        self.pushButton3.clicked.connect(lambda: self.Browser(file_filter="Image file (*.png *.bmp *.tiff *.jpg *.jpeg)", button_caption="Open World", input_field=self.inputworld))
        self.tab2_layout.addWidget(self.pushButton3)


        # Selecting world image
        self.outputsections = QLineEdit()
        self.tab2_layout.addRow(self.tr("Output folder for world sections:"), self.outputsections)    

        self.pushButtonSections = QPushButton("Select output folder for world sections")
        self.pushButtonSections.clicked.connect(lambda: self.Browser(file_filter="dir", button_caption="Open sections folder", input_field=self.outputsections))
        self.tab2_layout.addWidget(self.pushButtonSections)

        # Selecting output .json
        self.outputneighborrules = QLineEdit()
        self.tab2_layout.addRow(self.tr("Output neighbor filename:"), self.outputneighborrules)    

        self.pushButton4 = QPushButton("Select output neighbor file")
        self.pushButton4.clicked.connect(lambda: self.Browser(file_filter="JSON file(*.json)", button_caption="Write to ruleset", input_field=self.outputneighborrules))
        self.tab2_layout.addWidget(self.pushButton4)

        self.pushButtonGo2 = QPushButton("Detect tile neighbor ruleset")
        self.pushButtonGo2.clicked.connect(lambda: tileNBdetect(tile_folder=self.tilesetfolder.text(), world_name=self.inputworld.text(), sections_folder=self.outputsections.text(), output_file=self.outputneighborrules.text()))
        self.tab2_layout.addWidget(self.pushButtonGo2)

        self.tab2.setLayout(self.tab2_layout)
        
        
        # Create Tab 3: Wave collapse the world
        self.tab3_layout = QFormLayout(self.tab3)
        # Stap 3: Genereer wereld. Nodig: x en y, tileset map, regels-bestand, output file.
        # X worldsize
        
        self.worldSizeX = QLineEdit()
        self.tab3_layout.addRow(self.tr("Worldsize X:"), self.worldSizeX)
        # Y worldsize
        self.worldSizeY = QLineEdit()
        self.tab3_layout.addRow(self.tr("Worldsize Y:"), self.worldSizeY)

        # Tileset folder
        self.tilesetfolder2 = QLineEdit()
        self.tab3_layout.addRow(self.tr("Input tileset folder:"), self.tilesetfolder2)    

        self.pushButton5 = QPushButton("Select tileset folder")
        self.pushButton5.clicked.connect(lambda: self.Browser(file_filter="dir", button_caption="Open Tileset Folder", input_field=self.tilesetfolder2))
        self.tab3_layout.addWidget(self.pushButton5)

        # Neighbor rules
        self.inputneighborrules = QLineEdit()
        self.tab3_layout.addRow(self.tr("Input neighbor filename:"), self.inputneighborrules)    

        self.pushButton6 = QPushButton("Select input neighbor file")
        self.pushButton6.clicked.connect(lambda: self.Browser(file_filter="JSON file(*.json)", button_caption="Open neighbor ruleset", input_field=self.inputneighborrules))
        self.tab3_layout.addWidget(self.pushButton6)

        # Output world file
        self.inputworld2 = QLineEdit()
        self.tab3_layout.addRow(self.tr("Output world file:"), self.inputworld2)    

        self.pushButton7 = QPushButton("Select world output file")
        self.pushButton7.clicked.connect(lambda: self.Browser(file_filter="Image file (*.png *.bmp *.tiff *.jpg *.jpeg)", button_caption="Write World", input_field=self.inputworld2))
        self.tab3_layout.addWidget(self.pushButton7)

        self.visualGenerationToggle = QCheckBox("Show live world generation. Note: this may result in slower generation,\nespecially when the generator gets 'stuck' in a local problem.")
        self.tab3_layout.addWidget(self.visualGenerationToggle)
        
        self.pushButtonGo3 = QPushButton("Generate World")
        self.pushButtonGo3.clicked.connect(lambda: waveCollapse(tileset_folder=self.tilesetfolder2.text(), neighbor_rules_file=self.inputneighborrules.text(), xSize=int(self.worldSizeX.text()), ySize=int(self.worldSizeY.text()), show_generation=self.visualGenerationToggle.isChecked()))
        self.tab3_layout.addWidget(self.pushButtonGo3)

        # Finish up
        self.tab3.setLayout(self.tab3_layout)
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        # self.setLayout(self.layout)


    def Browser(self, file_filter, button_caption, input_field):
        if file_filter == "dir":
            folderName = QFileDialog.getExistingDirectory(parent=self, caption=button_caption, directory=getcwd())
            input_field.setText(folderName)
        else:    
            fileName, _ = QFileDialog.getOpenFileName(parent=self, caption=button_caption, directory=getcwd(), filter=file_filter)
            input_field.setText(fileName)

        
    def autoDetectToggle(self):
        value = self.toggleAutoDetect.isChecked()
        self.tileSize.setEnabled(not value)
        self.gridOffsetX.setEnabled(not value)
        self.gridOffsetY.setEnabled(not value)
        self.gridSize.setEnabled(not value)


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    app.exec()

"""
Stap 1: Import tileset en tip naar map vol individuele tiles. Nodig: input img (png, jpg), output folder. Vinkje auto-detect, of handmatig formaat invullen.
Stap 2: Koppel tileset terug in de wereld. Nodig: tileset map, wereld img. Output bestand met regels?
Stap 3: Genereer wereld. Nodig: x en y, tileset map, regels-bestand, output file.

"""