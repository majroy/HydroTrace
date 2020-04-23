#!/usr/bin/env python
'''
Trace hydrogen analyser main functions
-------------------------------------------------------------------------------
0.1 - Initial release
'''
__author__ = "M.J. Roy"
__version__ = "0.1"
__email__ = "matthew.roy@manchester.ac.uk"
__status__ = "Experimental"
__copyright__ = "(c) M. J. Roy, 2019-2020"

import sys, os.path, shutil, yaml
import subprocess as sp
from pkg_resources import Requirement, resource_filename
import numpy as np
import scipy.io as sio
from datetime import datetime
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

def read_cs_file(fname):
    """
    Reads the first two 'paragraphs' of a chem station file, returning the 
    following numpy arrays: int_run and area from the second paragraph and 
    dt, a list of datetime objects. The total number of runs can be indexed 
    from dt.
    """
    try:
        #get lines where data tables start and stop
        line_flag = []
        with open(fname, encoding='utf16') as f:
            for num, line in enumerate(f, 1):
                if "---|" in line:
                    line_flag.append(num)
        line_flag = np.asarray(line_flag)

        #debug
        # with open(fname, encoding='utf16') as f:
            # for num, line in enumerate(f, 1):
                # if num == line_flag[0]+1:
                    # print(line)
                # if num == line_flag[1]-7:
                    # print(line)
                # if num == line_flag[1]+1:
                    # print(line)
                # if num == line_flag[2]-1:
                    # print(line)


        #run through the file again with specific formatting applied
        dt = [] #date time for all runs
        int_run = [] #integrated run number
        area = []
        with open(fname, encoding='utf16') as f:
            i=1
            for num, line in enumerate(f, 1):
                if line_flag[0] < num < line_flag[1]-6: #1st paragraph
                    ls = line.strip().split()
                    dt.append(datetime.strptime(ls[3]+" "+ls[4],'%d/%m/%Y %H:%M:%S'))
                if line_flag[1] < num < line_flag[2]: #2nd paragraph
                    ls = line.strip().split()
                    if len(ls) == 8: #to handle extra characters in 2nd column
                        int_run.append(int(ls[0]))
                        area.append(float(ls[4]))
                    else:
                        int_run.append(int(ls[0]))
                        area.append(float(ls[5]))

        int_run = np.asarray(int_run)
        area = np.asarray(area)
        return int_run, area, dt #total number of runs indexed off of dt
    except:
        return None, None, None

def calc_total(hsc,std_pa,w,cgas,frate,ctime,area):
    """
    With H std content in ppm(hsc), H std peak area (std_pa), weight in g(w), carrier gas µmol/s (cgas),
    flow rate in mL/min (frate), cycle time in min (ctime) and area (from read_cs_file) returns
    total hydrogen content in ppm.
    """
    return np.sum((hsc*frate*(cgas*1e-6)*ctime*12/(std_pa*w))*area)
    # return (hsc*1e-6)*(area[0]/std_pa)*((frate/10)*cgas)*(1e6)/w*2*60

def get_file(*args):
    '''
    Returns absolute path to filename and the directory it is located in from a PyQt5 filedialog. First value is file extension, second is a string which overwrites the window message.
    '''
    ext = args[0]
    if len(args)>1:
        launchdir = args[1]
    else: launchdir = os.getcwd()
    ftypeName={}
    ftypeName['*.txt']=["Chem Station file:", "*.txt", "TXT File"]
        
    filer = QFileDialog.getOpenFileName(None, ftypeName[ext][0], 
         os.getcwd(),(ftypeName[ext][2]+' ('+ftypeName[ext][1]+');;All Files (*.*)'))

    if filer[0] == '':
        filer = None
        startdir = None
        return filer, startdir
        
    else: #return the filename/path
        return filer[0], os.path.dirname(filer[0])


class Ui_get_config_dialog(object):
    """
    Generates the pop-up window to manage default settings
    """
    def setupUi(self, get_config_dialog):
        # getFEAconfigDialog.resize(200, 200)
        get_config_dialog.setWindowTitle('Standard settings')
        get_config_dialog.setWindowIcon(QIcon(resource_filename("HydroTrace","meta/icon.png")))
        layout = QGridLayout(get_config_dialog)
        self.pushButton = QPushButton('Update')
        H_std_content_label = QLabel("Hydrogen standard content (ppm):")
        self.H_std_content=QDoubleSpinBox(get_config_dialog)
        Carrier_gas_molar_rate_label = QLabel("Carrier gas molar flow rate (µmol/s):")
        self.Carrier_gas_molar_rate=QDoubleSpinBox(get_config_dialog)
        
        self.file_loc = QLabel(get_config_dialog)
        self.file_loc.setFont(QFont("Helvetica",italic=True))
        self.file_loc.setWordWrap(True)
        
        layout.addWidget(H_std_content_label,0,0,1,1)
        layout.addWidget(self.H_std_content,0,1,1,1)
        layout.addWidget(Carrier_gas_molar_rate_label,1,0,1,1)
        layout.addWidget(self.Carrier_gas_molar_rate,1,1,1,1)
        
        
        
        layout.addWidget(self.pushButton,2,1,1,1)
        layout.addWidget(self.file_loc,3,0,1,2)
        
        self.pushButton.clicked.connect(lambda: self.make_config_change(get_config_dialog))


    def make_config_change(self, get_config_dialog):
        try:
            data= dict(FlowSettings = 
            dict( 
            content = self.H_std_content.value(), #61.00
            molar_rate = self.Carrier_gas_molar_rate.value() #7.44e-6
            )
            )
            print(data)
            with open(str(self.file_loc.text()), 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)
        except Exception as e:
            print(e)
            print("Configuration change failed.")
            

        get_config_dialog.close()

