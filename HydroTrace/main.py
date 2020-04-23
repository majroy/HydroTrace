#!/usr/bin/env python
'''
Trace hydrogen analyser interactor
-------------------------------------------------------------------------------
0.1 - Initial release
'''
__author__ = "M.J. Roy"
__version__ = "0.1"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2019-2020"

import os,io,sys,time,yaml
import subprocess as sp
from pkg_resources import Requirement, resource_filename
import numpy as np
import scipy.io as sio
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtGui, QtWidgets
#Change following to local import for dev
from HydroTrace.hydro_trace_common import *

        
class HT_main_window(object):
    """
    Class to build qt interaction, setupUi builds
    """
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle(("HydroTrace - v%s" %__version__))
        MainWindow.setMinimumWidth(800)
        MainWindow.setMinimumHeight(500)
        MainWindow.setWindowIcon(QtGui.QIcon(resource_filename("HydroTrace","meta/icon.png")))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.tabLayout = QtWidgets.QHBoxLayout(self.tabWidget)
        
        #add tabs
        self.ttltab = QtWidgets.QWidget(self.tabWidget)
        self.tabWidget.addTab(self.ttltab, "Total")
        self.othertab = QtWidgets.QWidget(self.tabWidget)
        self.tabWidget.addTab(self.othertab, "Other")
        #add footer
        horizLine=QtWidgets.QFrame()
        horizLine.setFrameStyle(QtWidgets.QFrame.HLine)
        image = QtWidgets.QLabel()
        image.setGeometry(QtCore.QRect(0, 0, 10, 10))
        pixmap = QtGui.QPixmap(resource_filename("HydroTrace","meta/InstitutionLogo.png"))
        pixmap.scaledToWidth(20)
        image.setPixmap(pixmap)
        image.show()
        self.settingsButton = QtWidgets.QPushButton('Settings')
        self.mainLayout.addWidget(horizLine)
        footerLayout = QtWidgets.QHBoxLayout()
        footerLayout.addWidget(image)
        footerLayout.addStretch()
        footerLayout.addWidget(self.settingsButton)
        self.mainLayout.addLayout(footerLayout)
        
        #populate ttl tab
        
        mainUiBox = QtWidgets.QGridLayout()
        
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(10)
    
        self.statLabel=QtWidgets.QLabel("Idle")
        self.statLabel.setWordWrap(True)
        self.statLabel.setFont(QtGui.QFont("Helvetica",italic=True))
        self.statLabel.setMinimumWidth(100)
        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.statLabel.sizePolicy().hasHeightForWidth())
        # self.statLabel.setSizePolicy(sizePolicy)

        headFont=QtGui.QFont("Helvetica [Cronyx]",weight=QtGui.QFont.Bold)
        
        
        #define buttons/widgets

        horizLine1=QtWidgets.QFrame()
        horizLine1.setFrameStyle(QtWidgets.QFrame.HLine)
        
        self.reloadButton = QtWidgets.QPushButton('Load')
        self.calcButton = QtWidgets.QPushButton('Calculate')
        
        
        labels = ['Hydrogen standard peak area:','Sample weight (g):','Gas flow rate during test (mL/min):','Cycle time of individual run (min):']

        self.spa = QtWidgets.QDoubleSpinBox()
        self.spa.setMaximum(10000000)
        self.spa.setMinimum(0)
        self.spa.setValue(86485)
        self.weight = QtWidgets.QDoubleSpinBox()
        self.weight.setValue(5)
        self.rate = QtWidgets.QDoubleSpinBox()
        self.rate.setValue(20)
        self.cycletime = QtWidgets.QDoubleSpinBox()
        self.cycletime.setValue(2.3)
        self.result = QtWidgets.QLineEdit('Undefined')
        #add widgets to ui
        
        mainUiBox.addWidget(self.reloadButton,0,0,1,1)
        mainUiBox.addWidget(self.calcButton,0,1,1,1)
        for i in range(0,4):
            mainUiBox.addWidget(QtWidgets.QLabel(labels[i]),2+i,0,1,1)
        
        mainUiBox.addWidget(self.spa,2,1,1,1)
        mainUiBox.addWidget(self.weight,3,1,1,1)
        mainUiBox.addWidget(self.rate,4,1,1,1)
        mainUiBox.addWidget(self.cycletime,5,1,1,1)
        mainUiBox.addWidget(horizLine1,6,0,1,2)
        mainUiBox.addWidget(QtWidgets.QLabel("Result (ppm)"),7,0,1,1)
        mainUiBox.addWidget(self.result,7,1,1,1)
        mainUiBox.addWidget(self.statLabel,8,0,1,2)
        
        ttlmainlayout = QtWidgets.QHBoxLayout()
        
        
        #plot
        self.figure = plt.figure(figsize=(2,2))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.ttltab)
        plt_layout = QVBoxLayout()
        plt_layout.addWidget(self.canvas)
        plt_layout.addWidget(self.toolbar)
        # plt_layout.addWidget(self.statLabel)
        
        ttlmainlayout.addLayout(mainUiBox)
        ttlmainlayout.addLayout(plt_layout)
        
        
        self.ttltab.setLayout(ttlmainlayout)
        
        
        
        #connections
        self.reloadButton.clicked.connect(lambda: self.get_input_data())
        self.calcButton.clicked.connect(lambda: self.calc())
        
        self.spa.valueChanged.connect(self.onValueChanged)
        self.weight.valueChanged.connect(self.onValueChanged)
        self.rate.valueChanged.connect(self.onValueChanged)
        self.cycletime.valueChanged.connect(self.onValueChanged)

        #load standards
        try:
            self.filec = resource_filename("HydroTrace","HydroTraceSettings.yml")
        except:
            print("Did not find config file in the pyCM installation directory.")
        try:
            with open(self.filec,'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader) 
        except:
            try:
                cfg= get_config([61.0,7.44],self.filec)
            except Exception as e:
                print(e)
                sys.exit("Failed to set config file. Quitting.")
        self.content = float(cfg['FlowSettings']['content'])
        self.flowconst = float(cfg['FlowSettings']['molar_rate'])
        self.settingsButton.clicked.connect(lambda: get_config([self.content,self.flowconst],self.filec))
        
    def get_input_data(self):
        
        
        filep,startdir=get_file('*.txt')
        if filep is None:
            return
        if not(os.path.isfile(filep)):
            print('Data file invalid.')
            return
        
        if filep != None: #because filediag can be cancelled
            self.cs_filename = filep
            self.statLabel.setText(filep)
            self.int_run, self.area, self.dt = read_cs_file(self.cs_filename)
            self.onValueChanged
        
    def calc(self):
        
        if hasattr(self,'area'):
            if self.area.any() != None:
                ans = calc_total(self.content, self.spa.value(),self.weight.value(),
                    self.flowconst,self.rate.value(),self.cycletime.value(),self.area)
                self.result.setText("%0.4f"%ans)
                
                #plot
                self.figure.clear()
                
                ax = self.figure.add_subplot(111)
                ax.scatter(self.int_run,self.area)
                ax.set_xlabel('Run number')
                ax.set_ylabel('Area (15 µV-s)')
                self.figure.tight_layout()
                self.canvas.draw()
                
            else:
                self.statLabel.setText('Invalid data.')
        else: self.statLabel.setText('No data read from file.')
    
    def onValueChanged(self):
        self.result.setText("Undefined")

    def keyPressEvent(self, event):
        if type(event) == QtGui.QKeyEvent:
            print(event.key)

    # def keyPressEvent(self, event):
        # if event.key() == QtCore.Qt.Key_Return:
            # print("keypress")
            # self.cfg=GetFEAconfig([y, 1, 4],"file")
        # event.accept()

def get_config(inputlist,filec):
    '''
    Creates a GUI window to let the user specify FEA executable paths and writes them to a config file. Reads configs.
    '''
    print(inputlist)
    get_config_dialog = QtWidgets.QDialog()
    dui = Ui_get_config_dialog()
    dui.setupUi(get_config_dialog)
    dui.H_std_content.setValue(inputlist[0])
    dui.Carrier_gas_molar_rate.setValue(inputlist[1])
    dui.file_loc.setText(filec)

    get_config_dialog.exec_()
    # getFEAconfigDialog.show()

    # try:
        # with open(filec,'r') as ymlfile:
            # return yaml.load(ymlfile, Loader=yaml.FullLoader)
    # except:
        # print("Couldn't read config file for some reason.")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    spl_fname=resource_filename("HydroTrace","meta/logo.png")
    splash_pix = QtGui.QPixmap(spl_fname,'PNG')
    splash = QtWidgets.QSplashScreen(splash_pix)
    splash.setMask(splash_pix.mask())

    splash.show()
    app.processEvents()
    MainWindow = QtWidgets.QMainWindow() 
    window = HT_main_window()
    window.setupUi(MainWindow)

    MainWindow.show()
    splash.finish(MainWindow)

    ret = app.exec_()
    
    if sys.stdin.isatty() and not hasattr(sys,'ps1'):
        del MainWindow
        sys.exit(ret)
