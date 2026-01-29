import os
import PyQt5
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
import PyQt5.QtWidgets as Qt# QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
import logging
import sys
import argparse
import ergastirio.widgets
import numpy as np
import pathlib
import datetime

import abstract_instrument_interface
import pyOceanopticsSpectrometer.driver
from pyOceanopticsSpectrometer.plots import PlotObject

graphics_dir = os.path.join(os.path.dirname(__file__), 'graphics')

class interface(abstract_instrument_interface.abstract_interface):
    """
    Create a high-level interface with the device, and act as a connection between the low-level
    interface (i.e. the driver) and the gui.
    Several general-purpose attributes and methods are defined in the class abstract_interface defined in abstract_instrument_interface
    ...

    Attributes specific for this class (see the abstract class abstract_instrument_interface.abstract_interface for general attributes)
    ----------
    instrument
        Instance of driver.ThorlabsPM100x
    connected_device_name : str
        Name of the physical device currently connected to this interface 
    continuous_read : bool 
        When this is set to True, the data from device are acquired continuosly at the rate set by integration_time
    integration_time : float, 
        The time interval (in seconds) between consecutive reeading from the device driver (default = 0.1)
    refresh_time : flaot
        refresh_time is always equal to integration_time for this instrument

    output : dict
        Dictionary containing the spectrum read by the this device (at a particular instant of time). It contains the following keys"

        wavelengths     : list of floats
        raw_spectrum    : list of floats
        background      : list of floats
        spectrum_background_corrected   : list of floats
        reference       : list of floats
        spectrum_background_corrected_normalized : list of floats


    Methods defined in this class (see the abstract class abstract_instrument_interface.abstract_interface for general methods)
    -------
    refresh_list_devices()
        Get a list of compatible devices from the driver. Stores them in self.list_devices, and populates the combobox in the GUI.
    connect_device(device_full_name)
        Connect to the device identified by device_full_name
    disconnect_device()
        Disconnect the currently connected device
    close()
        Closes this interface, close plot window (if any was open), and calls the close() method of the parent class, which typically calls the disconnect_device method
    
    set_disconnected_state()
        
    set_connecting_state()
    
    set_connected_state()
    
    set_refresh_time(refresh_time)
    
    
    start_reading()
    
    pause_reading()
    
    stop_reading()
    
    update()

    """

    output = {} #We define this also as class variable, to make it possible to see which data is produced by this interface without having to create an object

    ## SIGNALS THAT WILL BE USED TO COMMUNICATE WITH THE GUI
    #                                                           | Triggered when ...                                        | Parameter(s) Sent     
    #                                                       #   -----------------------------------------------------------------------------------------------------------------------         
    sig_list_devices_updated = QtCore.pyqtSignal(list)      #   | List of devices is updated                                | List of devices   
    sig_reading = QtCore.pyqtSignal(int)                    #   | Reading status changes                                    | 1 = Started Reading, 2 = Paused Reading, 3 Stopped Reading
    sig_does_device_have_TEC = QtCore.pyqtSignal(bool)       #  | New device is connected, inform if the device has TEC     | True = Device has TEC, False = Device does not have TEC  
    sig_temperature_read = QtCore.pyqtSignal(float)         #   | The temperature of the TEC has been read                  | Temperature    
    sig_updated_data = QtCore.pyqtSignal(object)            #   | Data is read from instrument                              | Acquired data 
    sig_integrationtime = QtCore.pyqtSignal(float)          #   | Integration time is changed                               | Current Integration time (in s)         
    sig_refreshtime = QtCore.pyqtSignal(float)              #   | Refresh time is changed                                   | Current Refresh time  (in s)
    sig_updated_data = QtCore.pyqtSignal(object)            #   | Data is read from instrument                              | Acquired data, as dictionary (see the output dictioray of this class)
    sig_background_acquired = QtCore.pyqtSignal(int)        #   | The background has been succesfully acquired              | 1
    sig_reference_acquired = QtCore.pyqtSignal(int)         #   | The reference has been succesfully acquired               | 1   
    sig_save_folder_updated = QtCore.pyqtSignal(str)        #   | The save folder has been correctly changed                | String containing the new save folder 
    sig_autosave_modality_changed = QtCore.pyqtSignal(str)  #   | The autosave modality changed                             | 'disabled', 'internal', 'external'
    ##
    # Identifier codes used for view-model communication. Other general-purpose codes are specified in abstract_instrument_interface
    SIG_READING_START = 1
    SIG_READING_PAUSE = 2
    SIG_READING_STOP = 3

    def __init__(self, **kwargs):
        self.output_internal = {    'wavelengths'                               : [0],
                                    'raw_spectrum'                              : [0],
                                    'background'                                : [0],
                                    'spectrum_background_corrected'             : [0],
                                    'reference'                                 : [0],
                                    'spectrum_background_corrected_normalized'  : [0]} 
        self.output = {}
        ### Default values of settings (might be overwritten by settings saved in .json files later)
        #Note: for this instrument the settings 'refresh_time' and 'integration_time' are actually the same (and their value is always identicaly). The setting 'refresh_time' is kept for legacy reasons
        self.settings = {   'backend' : 'pyseabreeze',
                            'refresh_time' : 0.1, #in seconds
                            'integration_time' : 0.1, #in seconds
                            'folder_save_data' : '',
                            'autosave': 'disabled'}
        
        self.list_devices = []          #list of devices found   
        self.connected_device_name = ''
        self.continuous_read = False    # When this is set to True, the data from device are acquired continuosly at the rate set by self.refresh_time
        self.continuous_refresh_TEC_temperature = True
        self.refresh_time_TEC_temperature = 1
        self.save_next_spectra_as_background = False
        self.save_next_spectra_as_reference = False
        
        ###
        self.instrument = pyOceanopticsSpectrometer.driver.OceanopticsSpectrometer() 
        ###
        super().__init__(**kwargs) #Here is when settings from .json file are loaded
        ###
        self.instrument.set_backend(self.settings['backend'])
        self.refresh_list_devices() 

############################################################
### Functions to interface the GUI and low-level driver
############################################################

    def refresh_list_devices(self):
        '''
        Get a list of all devices connected, by using the method list_devices() of the driver. For each device obtain its identity and its address.
        For each device, create the string "identity -->  address" and add the string to the corresponding combobox in the GUI 
        '''
        #self.gui.combo_Devices.clear()                      #First we empty the combobox       

        self.logger.info(f"Looking for devices...") 
        list_valid_devices = self.instrument.list_devices() #Then we read the list of devices
        self.logger.info(f"Found {len(list_valid_devices)} devices.") 
        self.list_devices = list_valid_devices
        self.send_list_devices()

        #if(len(list_valid_devices)>0):
        #    list_SNs_and_devices = [dev[1] + " --> " + dev[2] for dev in list_valid_devices] 
        #    self.gui.combo_Devices.addItems(list_SNs_and_devices)  

    def send_list_devices(self):
        if(len(self.list_devices)>0):
            list_IDNs_and_devices = [dev[1] + " --> " + dev[2] for dev in self.list_devices] 
        else:
            list_IDNs_and_devices = []
        self.sig_list_devices_updated.emit(list_IDNs_and_devices)
        
    def connect_device(self,device_full_name=None,device_serial_number=None):
        #The user can specify either the device_serial_number, or the device_full_name (which corresponds to the string shown in the combobox of the GUI)
        if(device_full_name==None and device_serial_number==None): 
            self.logger.error("No valid device has been selected.")
            return
        self.set_connecting_state()
        if device_serial_number==None:
            device_serial_number = device_full_name.split(' --> ')[0].lstrip()   # We extract the device serial number from the device name
        self.logger.info(f"Connecting to device {device_serial_number}...")
        try:
            connected = self.instrument.connect_device(device_serial_number)      # Try to connect by using the method ConnectDevice of the instrument object
            if connected :  #If connection was successful
                self.logger.info(f"Connected to device {device_serial_number}.")
                self.connected_device_name = device_serial_number
                self.set_connected_state()
                self.start_reading()
            else: #If connection was not successful
                self.logger.error(f"An unknown error occurred during connection.")
                self.set_disconnected_state()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.set_disconnected_state()

    def disconnect_device(self):
        try:
            self.logger.info(f"Disconnecting from device {self.connected_device_name}...")
            disconnected = self.instrument.disconnect_device()
            if disconnected: # If disconnection was successful
                self.continuous_refresh_TEC_temperature = False
                self.logger.info(f"Disconnected from device {self.connected_device_name}.")
                self.continuous_read = 0 # We set this variable to 0 so that the continuous reading  will stop
                self.set_disconnected_state()
            else: #If disconnection was not successful
                self.logger.error(f"An unknown error occurred during diconnection.")
                self.set_disconnected_state() #When disconnection is not succeful, it is typically because the device alredy lost connection
                                              #for some reason. In this case, it is still useful to have all widgets reset to disconnected state   
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.set_disconnected_state()
            
    def close(self,**kwargs):
#        if hasattr(self.gui,'plot_window'):
#            if self.gui.plot_window:
#                self.gui.plot_window.close()
        super().close(**kwargs)           
    
    def set_disconnected_state(self):
        self.continuous_refresh_TEC_temperature = False
        super().set_disconnected_state()

    def set_connected_state(self):
        super().set_connected_state()
        self.read_integration_time()
        if self.instrument.does_device_have_TEC:
            self.sig_does_device_have_TEC.emit(True)
            self.continuous_refresh_TEC_temperature = True
            self.update_TEC_temperature()
        else:
            self.sig_does_device_have_TEC.emit(False)
            self.continuous_refresh_TEC_temperature = False

    def set_refresh_time(self, refresh_time):
        self.set_integration_time(self, refresh_time)
        # try: 
        #     refresh_time = float(refresh_time)
        #     if self.settings['refresh_time'] == refresh_time: #in this case the number in the refresh time edit box is the same as the refresh time currently stored
        #         return True
        # except ValueError:
        #     self.logger.error(f"The refresh time must be a valid float number.")
        #     self.sig_refreshtime.emit(self.settings['refresh_time'])
        #     return False
        # if refresh_time < 0.001:
        #     self.logger.error(f"The refresh time must be positive and >= 1ms.")
        #     self.sig_refreshtime.emit(self.settings['refresh_time'])
        #     return False
        # self.logger.info(f"The refresh time is now {refresh_time} s.")
        # self.settings['refresh_time'] = refresh_time
        # self.sig_refreshtime.emit(self.settings['refresh_time'])
        # return True

    def set_integration_time(self, int_time):
        try: 
            int_time = float(int_time)
        except ValueError:
            self.logger.error(f"The integration time must be a valid float number.")
            self.read_integration_time()
            return False
        try:
            self.logger.info(f"Setting the integration time to {int_time}s for the device {self.connected_device_name}...")
            self.instrument.integration_time_microseconds = int(int_time*1e6)
            self.settings['integration_time'] = self.instrument.integration_time_microseconds
            self.settings['refresh_time'] = self.settings['integration_time']
            self.logger.info(f"Integration time set to {self.settings['integration_time']}.")
        except Exception as e:
            self.logger.error(f"An error occurred while setting the integration time: {e}")
            self.read_integration_time()
        return True

    def read_integration_time(self):
        try: 
            self.logger.info(f"Reading the integration time from the driver of the device {self.connected_device_name}...")
            self.settings['integration_time'] = self.instrument.integration_time_microseconds/1e6
            self.settings['refresh_time'] = self.settings['integration_time']
            self.logger.info(f"Current integration is {self.settings['integration_time']}s.")
        except Exception as e:
            self.logger.error(f"An error occurred while reading the integration time: {e}")
        self.sig_integrationtime.emit(self.settings['integration_time'])    
        self.sig_refreshtime.emit(self.settings['refresh_time'])
        return True

    def set_TEC_temperature(self, temperature):
        try: 
            self.logger.info(f"Setting the TEC temperature to {temperature} C for the device {self.connected_device_name}...")
            self.instrument.TEC_Temperature = temperature
            self.logger.info(f"TEC temperature set correctly.")
        except Exception as e:
            self.logger.error(f"An error occurred while setting the temperature: {e}")
            self.read_TEC_temperature()
        
    def read_TEC_temperature(self,log=True):
        if self.instrument.connected == False:
            return
        if log:
            self.logger.info(f"Reading current TEC temperature from device {self.connected_device_name}...") 
        self.TEC_temperature = self.instrument.TEC_Temperature
        if self.TEC_temperature == None:
            self.logger.error(f"An error occurred while reading the TEC temperature from this device. Maybe the device does not have a TEC?")
            return
        self.sig_temperature_read.emit(self.TEC_temperature)
        if log:
            self.logger.info(f"Current TEC temperature is {self.TEC_temperature} C.") 
        return
    
    def take_background(self):
        self.save_next_spectra_as_background = True

    def take_reference(self):
        self.save_next_spectra_as_reference = True

    def start_reading(self):
        if(self.instrument.connected == False):
            self.logger.error(f"No device is connected.")
            return
        
        self.sig_reading.emit(self.SIG_READING_START) # This signal will be caught by the GUI
        self.continuous_read = True #Until this variable is set to True, the function UpdatePower will be repeated continuosly 
        self.logger.info(f"Starting reading from device {self.connected_device_name}...")
        # Call the function self.update(), which will do stome suff (read spectrum and store it in a global variable) and then call itself continuosly until the variable self.continuous_read is set to False
        self.update()
        return
 
    def pause_reading(self):
        #Sets self.continuous_read to False (this will force the function update() to stop calling itself)
        self.continuous_read = False
        self.logger.info(f"Paused reading from device {self.connected_device_name}.")
        self.sig_reading.emit(self.SIG_READING_PAUSE) # This signal will be caught by the GUI
        return

    def stop_reading(self):
        #Sets self.continuous_read to False (this will force the function update() to stop calling itself) and delete all accumulated data
        self.continuous_read = False
        #self.stored_data = []
        self.update() #We call one more time the self.update() function to make sure plots is cleared. Since self.continuous_read is already set to False, update() will not acquire data anymore
        self.logger.info(f"Stopped reading from device {self.connected_device_name}. ")
        self.sig_reading.emit(self.SIG_READING_PAUSE) # This signal will be caught by the GUI
        # ...
        return
    
    def set_folder_save_data(self,folder,log=True):
        try: 
            folder = str(folder)
        except ValueError:
            if log: self.logger.error(f"The folder must be a valid string.")
            return False
        if pathlib.Path(folder).is_dir():
            self.settings['folder_save_data'] = folder
            if log: self.logger.info(f"Save folder is now {self.settings['folder_save_data']}")
            self.sig_save_folder_updated.emit(self.settings['folder_save_data'])
            return True
        else:
            if log: self.logger.error(f"The string '{self.settings['folder_save_data']}' is not a valid folder")
            return False
        
    def save_data(self,filename):  
        try: 
            filename = str(filename)
        except ValueError:
            self.logger.error(f"The filename must be a valid string.")
            return False  
        folder = self.settings['folder_save_data']
        if not(pathlib.Path(folder).is_dir()):
            self.logger.error(f"The current folder ('{folder}') is not a valid folder")
            return False
        
        date_to_write = ['raw_spectrum','spectrum_background_corrected','spectrum_background_corrected_normalized']
        data_to_write_appendix = ['raw','bkcgCorr','bkcgCorrNorm']

        for s_index,s in enumerate(date_to_write):
            if len(self.output_internal[s]) > 1:
                data = np.column_stack((self.output_internal['wavelengths'],self.output_internal[s]))
                fn = filename + '_' + data_to_write_appendix[s_index] + '.txt'
                path = os.path.join(folder,fn)
                try:
                    np.savetxt(path, data, fmt='%f')
                    self.logger.info(f"Saved {s} data in the file {path}")
                except Exception as e:
                    self.logger.error(f"An error occurred while saving the data\n: {e}")
                    return False
        return True

    def autosave_internal(self):
        # Everytime this function is called, it saves the current spectra on file
        now = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(now)
        self.save_data(timestamp)

    def receive_trigger(self,**kwargs):
        if self.settings['autosave'] == 'external':
            if 'timestamp' in kwargs.keys():
                timestamp = kwargs['timestamp']
            else:
                now = datetime.datetime.now()
                timestamp = datetime.datetime.timestamp(now)
            self.save_data(timestamp)

    def set_autosave_modality(self,status):
        # status can be 'disabled', 'internal', 'external'
        if status not in ['disabled', 'internal', 'external']:
            self.logger.error(f"Status not valid")  
            return False  
        self.logger.info(f"Autosave modality set to: {status}")
        self.settings['autosave'] = status
        self.sig_autosave_modality_changed.emit(self.settings['autosave'])
        return True

    def update(self):
        '''
        This routine reads continuosly the spectrum from the device
        If we are continuosly acquiring  (i.e. if self.ContinuousRead = 1) then:
            1) ...
            2)...
            3) ...
            3) Call itself after a time given by self.refresh_time
        '''
        if(self.continuous_read == True):
            (wl,spectrum) = self.instrument.spectrum
            self.output_internal['wavelengths'] = wl
            self.output_internal['raw_spectrum'] = spectrum

            if self.save_next_spectra_as_background:
                self.output_internal['background'] = spectrum 
                self.logger.info(f"Background Acquired")
                self.sig_background_acquired.emit(1)
                self.save_next_spectra_as_background = False
            if self.save_next_spectra_as_reference:
                self.output_internal['reference'] = spectrum 
                self.logger.info(f"Reference Acquired")
                self.sig_reference_acquired.emit(1)
                self.save_next_spectra_as_reference = False
            

            if len(self.output_internal['background'])>1:
                self.output_internal['spectrum_background_corrected'] = self.output_internal['raw_spectrum']  - self.output_internal['background']
                if len(self.output_internal['reference'])>1:
                    np.seterr(divide='ignore', invalid='ignore')
                    temp = np.divide(np.array(self.output_internal['spectrum_background_corrected']), np.array(self.output_internal['reference'] - self.output_internal['background'] )) 
                    np.seterr(divide='warn', invalid='warn')
                    self.output_internal['spectrum_background_corrected_normalized'] = temp.tolist()

            super().update()    
            QtCore.QTimer.singleShot(int(self.settings['refresh_time']*1e3), self.update)
            self.sig_updated_data.emit(self.output_internal)
            if self.settings['autosave'] == 'internal':
                self.autosave_internal()
        #if self.gui.plot_object:
        #    self.gui.plot_object.data.setData(self.output_internal['wavelengths'], self.output_internal['raw_spectrum']) #This line is executed even when self.continuous_read == False, to make sure that plot gets cleared when user press the stop button
        #   
        return

    def update_TEC_temperature(self):
        self.read_TEC_temperature(log=False)
        if(self.continuous_refresh_TEC_temperature == True):
            QtCore.QTimer.singleShot(int(self.refresh_time_TEC_temperature *1e3), self.update_TEC_temperature)
           
        return

############################################################
### END Functions to interface the GUI and low-level driver
############################################################
    
    
class gui(abstract_instrument_interface.abstract_gui):
     
    def __init__(self,interface,parent,is_main_window=False, plot=True):
        """
        Attributes specific for this class (see the abstract class abstract_instrument_interface.abstract_gui for general attributes)
        ----------
        plot, bool
            If set true, the GUI also generates a plot object (and a button to show/hide the plot) to plot the content of the self.stored_data object
        """
        super().__init__(interface,parent)
        self.plot_window = None # QWidget object of the widget (i.e. floating window) that will potentially contain the plot
        self.plot_object = False #Will be set to true if the plot_object has been created 

        self.is_main_window = is_main_window

        if plot:        # Create a plot object
            self.create_plot() #This will create all the Plot gui, and the object self.plots_container
            if not(is_main_window):
                #if the GUI is embedded in another GUI, the plots will be generated in another window
                self.plot_window = Qt.QWidget() #This is the widget that will contain the plot. Since it does not have a parent, the plot will be in a floating (separated) window
                self.plot_window.setLayout(self.plots_container)
                self.plot_window.show()
                self.plot_window.setHidden(True)
            
        self.initialize()

    def initialize(self):
        self.create_widgets()
        self.connect_widgets_events_to_functions()

        ### Call the initialize method of the super class. 
        super().initialize()

        ### Connect signals from model to event slots of this GUI
        self.interface.sig_list_devices_updated.connect(self.on_list_devices_updated)
        self.interface.sig_connected.connect(self.on_connection_status_change) 
        self.interface.sig_reading.connect(self.on_reading_status_change) 
        #self.interface.sig_refreshtime.connect(self.on_refreshtime_change)
        self.interface.sig_integrationtime.connect(self.on_integrationtime_change)
        self.interface.sig_updated_data.connect(self.on_data_change) 
        self.interface.sig_does_device_have_TEC.connect(self.on_TEC_change)
        self.interface.sig_background_acquired.connect(self.on_background_acquired)
        self.interface.sig_reference_acquired.connect(self.on_reference_acquired)
        self.interface.sig_temperature_read.connect(self.on_temperature_change)
        self.interface.sig_save_folder_updated.connect(self.on_save_folder_changed)
        self.interface.sig_autosave_modality_changed.connect(self.on_autosave_modality_changed)

        ### SET INITIAL STATE OF WIDGETS
        #self.edit_RefreshTime.setText(f"{self.interface.settings['refresh_time']:.3f}")
        self.interface.send_list_devices()  
        self.interface.set_autosave_modality(self.interface.settings['autosave'])
        self.interface.set_folder_save_data(self.interface.settings['folder_save_data'],log=False)
        self.on_connection_status_change(self.interface.SIG_DISCONNECTED) #When GUI is created, all widgets are set to the "Disconnected" state              
        ###


    def create_widgets(self):
        """
        Creates all widgets and layout for the GUI. Any Widget and Layout must assigned to self.containter, which is a pyqt Layout object
        """ 
        self.container = Qt.QVBoxLayout()

        #Use the custom connection/listdevices panel, defined in abstract_instrument_interface.abstract_gui
        hbox1 = Qt.QHBoxLayout() 
        _, widgets_dict = self.create_panel_connection_listdevices()
        widgets_stretches = [0,0,0,0]
        for w,s in zip(widgets_dict.values(),widgets_stretches):
            hbox1.addWidget(w,stretch=s)
        hbox1.addStretch(1)
        for key, val in widgets_dict.items(): 
            setattr(self,key,val)
        self.widgets_row_1 = widgets_dict.values()
        
        hbox2 = Qt.QHBoxLayout()  
        self.label_IntegrationTime = Qt.QLabel("Integration time (s): ")
        self.edit_IntegrationTime = Qt.QLineEdit()
        self.edit_IntegrationTime.setAlignment(QtCore.Qt.AlignRight)
        self.label_TECTemperature = Qt.QLabel("TEC Temperature (C): ")
        self.label_TECTemperature.setToolTip('Read/set the temperature of the TEC of this spectrometer, if available')
        self.label_TECTemperature_current = Qt.QLabel()
        self.label_TECTemperature_current.setFont( QtGui.QFont("Times", 12,QtGui.QFont.Bold) )
        self.label_TECTemperature_current.setToolTip('Current temperature of the TEC of this spectrometer (if TEC is available)')
        self.label_TECTemperature_setpoint = Qt.QLabel("Set point: ")
        self.label_TECTemperature_setpoint.setToolTip('Set temperature of the TEC of this spectrometer (if TEC is available)')
        self.edit_TECTemperature = Qt.QLineEdit()
        self.edit_TECTemperature.setToolTip('Set temperature of the TEC of this spectrometer (if TEC is available)')
       
        self.widgets_row_2 = [self.label_IntegrationTime,  self.edit_IntegrationTime, self.label_TECTemperature, self.label_TECTemperature_current,self.label_TECTemperature_setpoint, self.edit_TECTemperature]
        for w in self.widgets_row_2:
            hbox2.addWidget(w)
        hbox2.addStretch(1)

        hbox3 = Qt.QHBoxLayout()
        self.button_StartPauseReading = Qt.QPushButton("")
        self.button_StartPauseReading.setIcon(QtGui.QIcon(os.path.join(graphics_dir,'play.png')))
        self.button_StartPauseReading.setToolTip('Start or pause the reading.') 
        self.button_TakeReference = Qt.QPushButton("")
        self.button_TakeReference.setIcon(QtGui.QIcon(os.path.join(graphics_dir,'ligthON.png'))) 
        self.button_TakeReference.setToolTip('Acquire a reference spectra.') 
        self.button_TakeBackground = Qt.QPushButton("")
        self.button_TakeBackground.setIcon(QtGui.QIcon(os.path.join(graphics_dir,'ligthOFF.png'))) 
        self.button_TakeBackground.setToolTip('Acquire a background spectra.') 
        self.button_ShowHidePlot = Qt.QPushButton("Show/Hide Plot")
        self.button_ShowHidePlot.setToolTip('Show/Hide Plot.')
        self.widgets_row_3 = [self.button_StartPauseReading, self.button_TakeReference,self.button_TakeBackground,self.button_ShowHidePlot] 
        if not self.plot_window:
            self.button_ShowHidePlot.hide()
        for w in self.widgets_row_3:
            hbox3.addWidget(w)
        hbox3.addStretch(1)

        hbox4 = Qt.QHBoxLayout()
        self.button_ChooseFolder = Qt.QPushButton("Folder Data:")
        self.edit_FolderData = Qt.QLineEdit()
        self.edit_FolderData.setFixedWidth(300)
        self.edit_FolderData.setReadOnly(True)
        self.edit_FolderData.setAlignment(QtCore.Qt.AlignRight)
        self.edit_FilenameData = Qt.QLineEdit()
        self.edit_FilenameData.setFixedWidth(300)
        self.button_SaveData = Qt.QPushButton("Save")
        self.widgets_row_4 = [self.button_ChooseFolder,self.edit_FolderData,self.edit_FilenameData,self.button_SaveData] 
        for w in self.widgets_row_4:
            hbox4.addWidget(w)
        hbox4.addStretch(1)

        hbox5 = Qt.QHBoxLayout()
        self.label_AutoSave = Qt.QLabel("Autosave: ")
        self.radio_AutoSave = dict()
        self.radio_AutoSave['disabled'] = Qt.QRadioButton()
        self.radio_AutoSave['disabled'].setText("Disabled")
        self.radio_AutoSave['disabled'].value= "disabled"
        self.radio_AutoSave['disabled'].setChecked(True)
        self.radio_AutoSave['internal'] = Qt.QRadioButton()
        self.radio_AutoSave['internal'].setText("Internal")
        self.radio_AutoSave['internal'].value= "internal"
        self.radio_AutoSave['internal'].setToolTip('Everytime a spectra is acquired by the instrument, it is saved in a file (assuming that a valid folder has been selected). The name of the file will be determined by the current timestamp.') 
        self.radio_AutoSave['external'] = Qt.QRadioButton()
        self.radio_AutoSave['external'].setText("External")
        self.radio_AutoSave['external'].value= "external"
        self.radio_AutoSave['external'].setToolTip('Everytime this interface receives a trigger, it saves the current date on file (assuming that a valid folder has been selected). The name of the file will be determined by the string passed together with the external trigger.') 
        self.buttongroup_AutoSave = Qt.QButtonGroup(self.parent)
        for wd in self.radio_AutoSave.values():
            self.buttongroup_AutoSave.addButton(wd)
        self.widgets_row_5 = [self.label_AutoSave] + list(self.radio_AutoSave.values())
        for w in self.widgets_row_5:
            hbox5.addWidget(w)
        hbox5.addStretch(1)
    
        for box in [hbox1,hbox2,hbox3,hbox4,hbox5]:
            self.container.addLayout(box)  

        if self.is_main_window:
            self.container.addLayout(self.plots_container,1)  
        else:
            self.container.addStretch(1)

        self.widgets_enabled_when_connected = self.widgets_row_3+self.widgets_row_2
        self.widgets_disabled_when_connected = [self.button_RefreshDeviceList,self.combo_Devices]
        self.widgets_enabled_when_disconnected = self.widgets_row_1
        self.widgets_disabled_when_disconnected = self.widgets_row_3+self.widgets_row_2
        self.widgets_TEC = [self.label_TECTemperature,self.edit_TECTemperature,self.label_TECTemperature_setpoint,self.label_TECTemperature_current]

    def connect_widgets_events_to_functions(self):
        self.button_RefreshDeviceList.clicked.connect(self.click_button_refresh_list_devices)
        self.button_ConnectDevice.clicked.connect(self.click_button_connect_disconnect)
        self.edit_TECTemperature.returnPressed.connect(self.press_enter_TECtemperature)
        self.button_StartPauseReading.clicked.connect(self.click_button_StartPauseReading)
        self.edit_IntegrationTime.returnPressed.connect(self.press_enter_integration_time)
        self.button_TakeBackground.clicked.connect(self.click_button_take_background)
        self.button_TakeReference.clicked.connect(self.click_button_take_reference)
        self.button_ChooseFolder.clicked.connect(self.click_button_choose_folder)
        self.button_SaveData.clicked.connect(self.click_button_save_file)
        for wd in self.radio_AutoSave.values():
            wd.clicked.connect(self.click_radio_autosave)

        if self.plot_object:
            self.button_ShowHidePlot.clicked.connect(self.click_button_ShowHidePlot)

    def show_hide_TEC_widgets(self,enabled):
        if enabled:
            self.enable_widget(self.widgets_TEC)
        else:
            self.disable_widget(self.widgets_TEC)

    ###########################################################################################################
    ### Event Slots. They are normally triggered by signals from the model, and change the GUI accordingly  ###
    ###########################################################################################################

    def on_connection_status_change(self,status):
        if status == self.interface.SIG_DISCONNECTED:
            self.disable_widget(self.widgets_disabled_when_disconnected)
            self.enable_widget(self.widgets_enabled_when_disconnected)
            self.button_ConnectDevice.setText("Connect")
        if status == self.interface.SIG_DISCONNECTING:
            self.disable_widget(self.widgets_disabled_when_disconnected)
            self.enable_widget(self.widgets_enabled_when_disconnected)
            self.button_ConnectDevice.setText("Disconnecting...")
        if status == self.interface.SIG_CONNECTING:
            self.disable_widget(self.widgets_disabled_when_disconnected)
            self.enable_widget(self.widgets_enabled_when_disconnected)
            self.button_ConnectDevice.setText("Connecting...")
        if status == self.interface.SIG_CONNECTED:
            self.disable_widget(self.widgets_disabled_when_connected)
            self.enable_widget(self.widgets_enabled_when_connected)
            self.button_ConnectDevice.setText("Disconnect")
            
            if self.plot_object: 
                styles = {"color": "#fff", "font-size": "20px"}
                if self.plot_window:
                    self.plot_window.setWindowTitle(f"Instrument: {self.interface.connected_device_name}")

                wavelength_label = f"Wavelength ({self.interface.instrument.wavelength_units})"

                self.plot_objects[0].data_headers=[wavelength_label,'Counts']
                self.plot_objects[0].plot_config = {"x": wavelength_label, "y": ['Counts']}

                self.plot_objects[1].data_headers=[wavelength_label,'Counts']
                self.plot_objects[1].plot_config = {"x": wavelength_label, "y": ['Counts']}

                self.plot_objects[2].data_headers=[wavelength_label,'Relative (%)']
                self.plot_objects[2].plot_config = {"x": wavelength_label, "y":  ['Relative (%)']}

    def on_reading_status_change(self,status):
        if status == self.interface.SIG_READING_PAUSE:
            self.button_StartPauseReading.setIcon(QtGui.QIcon(os.path.join(graphics_dir,'play.png')))
        if status == self.interface.SIG_READING_START:
            self.button_StartPauseReading.setIcon(QtGui.QIcon(os.path.join(graphics_dir,'pause.png')))
        if status == self.interface.SIG_READING_STOP: 
            self.button_StartPauseReading.setIcon(QtGui.QIcon(os.path.join(graphics_dir,'play.png')))

    def on_list_devices_updated(self,list_devices):
        self.combo_Devices.clear()  #First we empty the combobox  
        self.combo_Devices.addItems(list_devices) 

    #def on_refreshtime_change(self,value):
    #    self.edit_RefreshTime.setText(f"{value:.3f}")

    def on_integrationtime_change(self,value):
        self.edit_IntegrationTime.setText(f"{value:.4f}")

    def on_data_change(self,data):
        data_list = [data['wavelengths'], data['raw_spectrum']]
        self.plot_objects[0].data = list(zip(*data_list)) 
        if len(data['spectrum_background_corrected']) > 1:
            data_list = [data['wavelengths'], data['spectrum_background_corrected']]
            self.plot_objects[1].data = list(zip(*data_list)) 
        if len(data['spectrum_background_corrected_normalized']) > 1:
            data_list = [data['wavelengths'], data['spectrum_background_corrected_normalized']]
            self.plot_objects[2].data = list(zip(*data_list)) 

    def on_TEC_change(self,available):
        self.show_hide_TEC_widgets(enabled=available)

    def on_background_acquired(self):
        if not(self.plot_window_tab_object.currentIndex())==2:
            self.plot_window_tab_object.setCurrentIndex(1)

    def on_reference_acquired(self):
        self.plot_window_tab_object.setCurrentIndex(2)

    def on_temperature_change(self,value):
        self.label_TECTemperature_current.setText(str(value))

    def on_save_folder_changed(self,text):
        #info = data[:75] + (data[75:] and '..')
        self.edit_FolderData.setText(f"{text}")

    def on_autosave_modality_changed(self,status):
        self.radio_AutoSave[status].setChecked(True)

    #######################
    ### END Event Slots ###
    #######################


            
############################################################
### GUI Events Functions
############################################################

    def click_button_refresh_list_devices(self):
        self.interface.refresh_list_devices()

    def click_button_connect_disconnect(self):
        if(self.interface.instrument.connected == False): # We attempt connection   
            device_full_name = self.combo_Devices.currentText() # Get the device name from the combobox
            self.interface.connect_device(device_full_name)
        elif(self.interface.instrument.connected == True): # We attempt disconnection
            self.interface.disconnect_device()

    def press_enter_TECtemperature(self):
        return self.interface.set_TEC_temperature(self.edit_TECTemperature.text())
        
    def click_button_change_power_range(self,direction):
        self.interface.change_power_range(direction)

    def click_button_take_background(self):
        self.interface.take_background()

    def click_button_take_reference(self):
        self.interface.take_reference()
       
    def click_button_StartPauseReading(self): 
        if(self.interface.continuous_read == False):
            if not(self.press_enter_integration_time): #read the current value in the refresh_time textbox, and validates it. The function returns True/False if refresh_time was valid
                return
            self.interface.start_reading()
        elif (self.interface.continuous_read == True):
            self.interface.pause_reading()
        return

    def press_enter_refresh_time(self):
        return self.interface.set_refresh_time(self.edit_RefreshTime.text())

    def press_enter_integration_time(self):
        return self.interface.set_integration_time(self.edit_IntegrationTime.text())

    def click_button_ShowHidePlot(self):
        self.plot_window.setHidden(not self.plot_window.isHidden())

    def click_button_choose_folder(self):
        current_path = self.interface.settings['folder_save_data']
        folderpath = Qt.QFileDialog.getExistingDirectory(self.parent, 'Select Folder',current_path)
        if folderpath:
            return self.interface.set_folder_save_data(folderpath)
        else:
            return False
        
    def click_button_save_file(self):
        if len(self.edit_FilenameData.text())>0:
            self.interface.save_data(self.edit_FilenameData.text())

    def click_radio_autosave(self,status):
        for wd_name in self.radio_AutoSave.keys():
            if self.radio_AutoSave[wd_name].isChecked():
                self.interface.set_autosave_modality(wd_name)
                return


############################################################
### END GUI Events Functions
############################################################

    def create_plot(self):
        '''
        This function creates an additional (separated) window with a pyqtgraph object, which plots the contents of self.stored_data
        '''
        self.plot_object = True
        
        PlotNames = ['Raw','Raw Minus Background','Relative']

        self.plots_container = Qt.QVBoxLayout()
        self.plot_window_tab_object = Qt.QTabWidget()
        self.plots_container.addWidget(self.plot_window_tab_object)

        self.plot_window_tabs = []
        self.plot_objects = []
        self.plot_window_tab_containers = []
        for i in range(len(PlotNames)):
            NewTab = Qt.QWidget()
            self.plot_window_tabs.append(NewTab)   
            self.plot_window_tab_containers.append(Qt.QVBoxLayout())
            self.plot_window_tab_object.addTab(NewTab,PlotNames[i])
            NewPlot = ergastirio.widgets.PlotObject(NewTab)
            NewPlot.create_styles(symbol = None,colors = 'bgwcmyw')
            NewPlot.controlWidget.toolButton_X.hide()
            NewPlot.controlWidget.toolButton_Y.hide()
            NewPlot.show_legend = False
            self.plot_objects.append(NewPlot)

        wavelength_label = f"Wavelength (nm)"
        self.plot_objects[0].data_headers=[wavelength_label,'Counts']
        self.plot_objects[0].plot_config = {"x": wavelength_label, "y": ['Counts']}
        self.plot_objects[1].data_headers=[wavelength_label,'Counts']
        self.plot_objects[1].plot_config = {"x": wavelength_label, "y": ['Counts']}
        self.plot_objects[2].data_headers=[wavelength_label,'Relative (%)']
        self.plot_objects[2].plot_config = {"x": wavelength_label, "y":  ['Relative (%)']}

class MainWindow(Qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__package__)

    def closeEvent(self, event):
        #if self.child:
            pass#self.child.close()

#################################################################################################

def main():
    parser = argparse.ArgumentParser(description = "",epilog = "")
    parser.add_argument("-s", "--decrease_verbose", help="Decrease verbosity.", action="store_true")
    parser.add_argument('-virtual', help=f"Initialize the virtual driver", action="store_true")
    args = parser.parse_args()
    virtual = args.virtual

    app = Qt.QApplication(sys.argv)
    window = MainWindow()
    Interface = interface(app=app,virtual=virtual) 
    Interface.verbose = not(args.decrease_verbose)
    app.aboutToQuit.connect(Interface.close)  
    view = gui(interface = Interface, parent=window, is_main_window = True, plot=True) 
    #is_main_window = True tells the GUI that it is not contained inside another window. This is used to let the gui decide whether to show the plot panel in a separate window or not
    window.show()
    app.exec()# Start the event loop.

if __name__ == '__main__':
    main()

#################################################################################################
