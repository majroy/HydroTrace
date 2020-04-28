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

import os,io,sys,time,yaml,ctypes
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
        MainWindow.setMinimumWidth(600)
        MainWindow.setMinimumHeight(600)
        MainWindow.setWindowIcon(QtGui.QIcon(resource_filename("HydroTrace","meta/icon.png")))
        myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) #windows taskbar icon
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.tabLayout = QtWidgets.QHBoxLayout(self.tabWidget)
        
        #add tabs
        self.ttltab = QtWidgets.QWidget(self.tabWidget)
        self.tabWidget.addTab(self.ttltab, "Basic")
        self.temptab = QtWidgets.QWidget(self.tabWidget)
        self.tabWidget.addTab(self.temptab, "Temperature")
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
        
        #declare any title font
        headFont=QtGui.QFont("Helvetica [Cronyx]",weight=QtGui.QFont.Bold)
        
        #------------------------------------------------------------
        #populate ttl tab
        #------------------------------------------------------------
        mainUiBox = QtWidgets.QGridLayout()
        
    
        self.statLabel=QtWidgets.QLabel("Idle")
        self.statLabel.setWordWrap(True)
        self.statLabel.setFont(QtGui.QFont("Helvetica",italic=True))

        #define buttons/widgets

        horizLine1=QtWidgets.QFrame()
        horizLine1.setFrameStyle(QtWidgets.QFrame.HLine)
        
        self.reloadButton = QtWidgets.QPushButton('Load')
        self.calcButton = QtWidgets.QPushButton('Calculate')
        self.calcButton.resize(self.calcButton.sizeHint())
        
        
        labels = ['Hydrogen standard peak area:','Sample weight (g):','Gas flow rate during test (mL/min):','Cycle time of individual run (min):']

        self.spa = QtWidgets.QDoubleSpinBox()
        self.spa.setMaximum(10000000)
        self.spa.setMinimum(0)
        self.spa.setValue(0)
        self.weight = QtWidgets.QDoubleSpinBox()
        self.weight.setValue(0)
        self.rate = QtWidgets.QDoubleSpinBox()
        self.rate.setValue(0)
        self.cycletime = QtWidgets.QDoubleSpinBox()
        self.cycletime.setValue(0)
        self.result = QtWidgets.QLineEdit('Undefined')
        #add widgets to ui
        
        mainUiBox.addWidget(self.reloadButton,0,0,1,1)
        mainUiBox.addWidget(self.calcButton,1,0,1,1)
        for i in range(0,4):
            mainUiBox.addWidget(QtWidgets.QLabel(labels[i]),3+i,0,1,1)
        
        mainUiBox.addWidget(self.spa,3,1,1,1)
        mainUiBox.addWidget(self.weight,4,1,1,1)
        mainUiBox.addWidget(self.rate,5,1,1,1)
        mainUiBox.addWidget(self.cycletime,6,1,1,1)
        mainUiBox.addWidget(horizLine1,7,0,1,2)
        mainUiBox.addWidget(QtWidgets.QLabel("Result (ppm)"),8,0,1,1)
        mainUiBox.addWidget(self.result,8,1,1,1)
        mainUiBox.addWidget(self.statLabel,10,0,1,2)
        
        ttlmainlayout = QtWidgets.QHBoxLayout()
        
        
        #plot
        self.figure1 = plt.figure(figsize=(2,2))
        self.canvas1 = FigureCanvas(self.figure1)
        self.toolbar1 = NavigationToolbar(self.canvas1, self.ttltab)
        plt_layout1 = QVBoxLayout()
        plt_layout1.addWidget(self.canvas1)
        plt_layout1.addWidget(self.toolbar1)
        # plt_layout.addWidget(self.statLabel)
        
        ttlmainlayout.addLayout(mainUiBox)
        # ttlmainlayout.addStretch()
        ttlmainlayout.addLayout(plt_layout1)
        
        self.ttltab.setLayout(ttlmainlayout)
        
        #------------------------------------------------------------
        #populate temp tab
        #------------------------------------------------------------
        tempUiButtonBox = QtWidgets.QGridLayout()
        
        self.tempLabel=QtWidgets.QLabel("Idle")
        self.tempLabel.setWordWrap(True)
        self.tempLabel.setFont(QtGui.QFont("Helvetica",italic=True))
        
        self.loadTempButton = QtWidgets.QPushButton('Load')
        self.calcTempButton = QtWidgets.QPushButton('Calculate')
        self.calcTempButton.setEnabled(False)
        self.DvsTempButton=QtWidgets.QRadioButton("Desorbtion vs. Temp")
        self.DvsTimeButton=QtWidgets.QRadioButton("Desorbtion vs. Time")
        self.TvsTimeButton=QtWidgets.QRadioButton("Temp vs. Time")
        self.DvsTempButton.setChecked(True)
        plottingButtonGroup = QtWidgets.QButtonGroup()
        plottingButtonGroup.addButton(self.DvsTempButton)
        plottingButtonGroup.addButton(self.DvsTimeButton)
        plottingButtonGroup.addButton(self.TvsTimeButton)
        plottingButtonGroup.setExclusive(True)
        plottingBoxlayout = QtWidgets.QGridLayout()
        plottingBoxlayout.addWidget(self.DvsTempButton,1,1)
        plottingBoxlayout.addWidget(self.DvsTimeButton,2,1)
        plottingBoxlayout.addWidget(self.TvsTimeButton,3,1)
        
        self.delay = QtWidgets.QDoubleSpinBox()
        self.delay.setValue(0)
        
        self.exportButton = QtWidgets.QPushButton('Export')
        self.exportButton.setEnabled(False)
        
        tempUiButtonBox.addWidget(self.loadTempButton,0,0,1,1)
        tempUiButtonBox.addWidget(self.calcTempButton,0,1,1,1)
        tempUiButtonBox.addWidget(QtWidgets.QLabel("Temperature delay (m):"),1,0,1,1)
        tempUiButtonBox.addWidget(self.delay,1,1,1,1)
        tempUiButtonBox.addLayout(plottingBoxlayout,2,0,1,2)
        tempUiButtonBox.addWidget(self.exportButton,4,0,1,1)
        
        tempUiButtonBox.addWidget(self.tempLabel,6,0,1,2)
        
        tempmainlayout = QtWidgets.QHBoxLayout()
        
        #plot
        self.figure2 = plt.figure(figsize=(2,2))
        self.canvas2 = FigureCanvas(self.figure2)
        self.toolbar2 = NavigationToolbar(self.canvas2, self.temptab)
        plt_layout2 = QVBoxLayout()
        plt_layout2.addWidget(self.canvas2)
        plt_layout2.addWidget(self.toolbar2)
        # plt_layout.addWidget(self.statLabel)
        
        tempmainlayout.addLayout(tempUiButtonBox)
        tempmainlayout.addLayout(plt_layout2)
        
        
        self.temptab.setLayout(tempmainlayout)
        
        #------------------------------------------------------------
        #connections
        #------------------------------------------------------------
        self.reloadButton.clicked.connect(lambda: self.get_input_data())
        self.loadTempButton.clicked.connect(lambda: self.get_input_temp_data())
        self.calcButton.clicked.connect(lambda: self.calc())
        self.calcTempButton.clicked.connect(lambda: self.calc_temp())
        self.exportButton.clicked.connect(lambda: self.export())
        
        self.spa.valueChanged.connect(self.onValueChanged)
        self.weight.valueChanged.connect(self.onValueChanged)
        self.rate.valueChanged.connect(self.onValueChanged)
        self.cycletime.valueChanged.connect(self.onValueChanged)

        self.DvsTempButton.clicked.connect(lambda: self.update_temptab_plot('DvsTemp'))
        self.DvsTimeButton.clicked.connect(lambda: self.update_temptab_plot('DvsTime'))
        self.TvsTimeButton.clicked.connect(lambda: self.update_temptab_plot('TvsTime'))

        #------------------------------------------------------------
        #load standards
        #------------------------------------------------------------
        try:
            self.filec = resource_filename("HydroTrace","HydroTraceSettings.yml")
        except:
            print("Did not find config file in the installation directory.")
        try:
            with open(self.filec,'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader) 
        except Exception as e:
            print('Failed load',e)
            try:
                cfg= get_config([61.0,7.44],self.filec)
            except Exception as e:
                print(e)
                sys.exit("Failed to set config file. Quitting.")
        self.content = float(cfg['FlowSettings']['content'])
        self.flowconst = float(cfg['FlowSettings']['molar_rate'])
        self.settingsButton.clicked.connect(lambda: get_config([],self.filec))
        
    def get_input_temp_data(self):
        """
        Gets a valid temperature file
        """
        
        filep,startdir=get_file('*.csv')
        if filep is None:
            return
        if not(os.path.isfile(filep)):
            print('Data file invalid.')
            return
        
        if filep != None: #because filediag can be cancelled
            self.temp_filename = filep
            self.tempLabel.setText(filep)
            self.temp, self.temp_dt = read_pico_csv(self.temp_filename)
        
    def get_input_data(self):
        """
        Gets a valid GC file and reads contents
        """
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
    
    def export(self):
        """
        Collects data from ui, gets a valid file to write to.
        """
        
        fileo,startdir=get_save_file('*.htd',None)
        if fileo is None:
            return
        
        if fileo != None: #because filediag can be cancelled
            np.savetxt(fileo,
            np.column_stack((self.common_time,self.common_temp,self.d_rate)), 
            delimiter=',',
            header = "Time (min),Temp (°C), D_rate (ppm/min)")
    
    def calc(self):
        """
        Calculate total H content, make plot in tab 1
        """
        if hasattr(self,'area'):
            if self.area.any() != None:
                ans = calc_total(self.content, self.spa.value(),self.weight.value(),
                    self.flowconst,self.rate.value(),self.cycletime.value(),self.area)
                self.result.setText("%0.4f"%ans)
                
                #plot
                self.figure1.clear()
                
                ax = self.figure1.add_subplot(111)
                ax.scatter(self.int_run,self.area)
                ax.set_xlabel('Run number')
                ax.set_ylabel('Area (15 µV-s)')
                ax.grid(b=True, which='major', color='#666666', linestyle='-')
                ax.minorticks_on()
                ax.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
                self.figure1.tight_layout()
                self.canvas1.draw()
                self.calcTempButton.setEnabled(True) #temperature calculation can happen
            else:
                self.statLabel.setText('Invalid data.')
        else: self.statLabel.setText('No data read from file.')
    
    def calc_temp(self):
        """
        Based on read-in temperature and datetime values, linearly interpolate these temperature values on a delayed delayed temperature datetime series. Zeroes overall time on the basis of the earliest datetime recorded between both GC and temperature records, converting time records from datetime to float values in minutes for plotting.
        """
        if hasattr(self,'temp'):
            if self.temp.any() != None:
                #get delay
                tempdelay = timedelta(minutes=self.delay.value())
                delayed_time = [tempdelay + times for times in self.temp_dt]
                self.common_temp, self.common_time, = interp_datetime(delayed_time,self.temp,[self.dt[j] for j in self.int_run+1])
                self.d_rate = calc_desorbtion_rate(self.content, self.spa.value(),self.weight.value(),
                    self.flowconst,self.rate.value(),self.area)
                #adjust mdates to minutes and zero off of earliest datetime
                self.temp_time = mdates.date2num(self.temp_dt)
                mintime = np.min(np.append(self.common_time,self.temp_time))
                self.common_time = (self.common_time - mintime)*1440 #minutes
                self.temp_time = (self.temp_time - mintime)*1440 #minutes
                #update ui
                self.DvsTempButton.setChecked(True)
                self.update_temptab_plot('DvsTemp')
                self.exportButton.setEnabled(True)
            else:
                self.tempLabel.setText('Invalid data.')
        else: self.tempLabel.setText('No data read from file.')

    def update_temptab_plot(self,s):
        """
        Updates plots in temperature tab
        """
        if hasattr(self,'common_time') != None:
            #plot
            self.figure2.clear()
            ax = self.figure2.add_subplot(111)
            ax.grid(b=True, which='major', color='#666666', linestyle='-')
            ax.minorticks_on()
            ax.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
            if s == 'DvsTemp':
                ax.scatter(self.common_temp,self.d_rate,color=((0.3,0,0.6,1)) )
                ax.axis(ymin = 0, ymax = 1.1*self.d_rate.max())
                ax.set_xlabel('Temperature (°C)')
                ax.set_ylabel('Desorbtion rate (ppm/min)')
            elif s == 'DvsTime':
                ax.scatter(self.common_time,self.d_rate, color=((0,0.7,1,1)) )
                ax.axis(ymin = 0, ymax = 1.1*self.d_rate.max())
                ax.set_xlabel('Time (min)')
                ax.set_ylabel('Desorbtion rate (ppm/min)')
            elif s == 'TvsTime':
                ax.scatter(self.common_time,self.common_temp, s=50, color=((1,0.549,0,1)),label = 'Common' )
                ax.scatter(self.temp_time,self.temp, s=10, color=((1,0.647,0,0.25)), label = 'Raw' )
                ax.axis(ymin = 0, ymax = 1.1*self.temp.max())
                ax.legend(loc='upper left');
                ax.set_xlabel('Time (min)')
                ax.set_ylabel('Temperature (°C)')
            self.figure2.tight_layout()
            self.figure2.autofmt_xdate()
            self.canvas2.draw()
            
    def onValueChanged(self):
        """
        Changes result box if any inputs are changed in the basic tab, and clear the figure in temp tab
        """
        self.result.setText("Undefined")
        self.figure2.clear()


def get_config(inputlist,filec):
    '''
    Creates a GUI window to let the user specify a config file. Reads configs.
    '''
    if inputlist == []:
        with open(filec,'r') as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        inputlist = [float(cfg['FlowSettings']['content']), float(cfg['FlowSettings']['molar_rate'])]
    get_config_dialog = QtWidgets.QDialog()
    dui = Ui_get_config_dialog()
    dui.setupUi(get_config_dialog)
    dui.H_std_content.setValue(inputlist[0])
    dui.Carrier_gas_molar_rate.setValue(inputlist[1])
    dui.file_loc.setText(filec)

    get_config_dialog.exec_()

#Run as main
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
