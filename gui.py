from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QFormLayout, QTabWidget, QFileDialog, QCheckBox, QLabel, QLineEdit
from os import getcwd

# Create the app's main window
class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # Title
        self.setWindowTitle("Waves")

        # Window size
        self.left = 0
        self.top = 0
        self.width = 400
        self.height = 300
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
        self.tab1.layout = QFormLayout(self)
        self.inputfilename = QLineEdit()
        self.tab1.layout.addRow(self.tr("Input tileset filename:"), self.inputfilename)    

        self.pushButton1 = QPushButton("Select tileset")
        self.pushButton1.clicked.connect(self.TilesetBrowser)
        self.tab1.layout.addWidget(self.pushButton1)

        # Toggle for autodetecting the grid of the tileset
        self.toggleAutoDetect = QCheckBox("Autodetect Tile- and Gridsize")
        self.toggleAutoDetect.clicked.connect(self.autoDetectToggle)
        self.tab1.layout.addWidget(self.toggleAutoDetect)
        self.toggleAutoDetect.setChecked(True)
        
        # For manual parameters for grid detection
        self.tileSizeX = QLineEdit("Tilesize X in px")
        self.tab1.layout.addWidget(self.tileSizeX)
        self.tileSizeY = QLineEdit("Tilesize Y in px")
        self.tab1.layout.addWidget(self.tileSizeY)

        self.gridOffsetX = QLineEdit("Grid offset X in px")
        self.tab1.layout.addWidget(self.gridOffsetX)
        self.gridOffsetY = QLineEdit("Grid offset Y in px")
        self.tab1.layout.addWidget(self.gridOffsetY)
        self.gridWidth = QLineEdit("Grid width in px")
        self.tab1.layout.addWidget(self.gridWidth)
        
        self.autoDetectToggle()
        self.tab1.setLayout(self.tab1.layout)

        # Create Tab 2: determining the rules of the world by matching tileset in world
        self.tab2.layout = QFormLayout(self)
        self.pushButton2 = QPushButton("PyQt5 button")
        self.tab2.layout.addWidget(self.pushButton2)
        self.tab2.setLayout(self.tab2.layout)
        
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        # self.setLayout(self.layout)

    def TilesetBrowser(self):
        file_filter = "Image file (*.png *.bmp *.tiff *.jpg *.jpeg)"
        fileName, _ = QFileDialog.getOpenFileName(parent=self, caption= "Open Tileset", directory=getcwd(), filter=file_filter)
        self.inputfilename.setText(fileName)
        
    def autoDetectToggle(self):
        value = self.toggleAutoDetect.isChecked()
        self.tileSizeX.setEnabled(not value)
        self.tileSizeY.setEnabled(not value)
        self.gridOffsetX.setEnabled(not value)
        self.gridOffsetY.setEnabled(not value)
        self.gridWidth.setEnabled(not value)


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    app.exec()

"""
Stap 1: Import tileset en tip naar map vol individuele tiles. Nodig: input img (png, jpg), output folder. Vinkje auto-detect, of handmatig formaat invullen.
Stap 2: Koppel tileset terug in de wereld. Nodig: tileset map, wereld img. Output bestand met regels?
Stap 3: Genereer wereld. Nodig: x en y, tileset map, regels-bestand, output file.

"""