import seabreeze
from seabreeze.spectrometers import Spectrometer, list_devices

class OceanopticsSpectrometer:

    def __init__(self,model=None):
        self.connected = False
        self.model = None       #model of the device currently connected. 
        self._wavelengths = None
        self._intensities = None
        self.device = None # Spectrometer object describing the device currently coonected
        self._integration_time_microseconds = 100000 #default value, 100ms
        self._integration_time_limits_microseconds = None
        self.does_device_have_TEC = False 
        
    def set_backend(self,backend):
        if backend not in ['cseabreeze', 'pyseabreeze']: 
            raise RuntimeError("Backend name not valid. Possible values are cseabreeze and pyseabreeze")
        seabreeze.use(backend)
        
    def list_devices(self):
        '''
        Returns
        -------
        list_devices_identifier, list
            A list of all found valid devices. Each element of the list is a list of three element, in the format [ID,serialnumber,model], where ID is just an increasing integer

        '''
        self.list_spectrometers = list_devices()
        self.list_devices_identifier = [] 
        for ID, device in enumerate(self.list_spectrometers):
            self.list_devices_identifier.append([ID,device.serial_number,device.model])
            
        return self.list_devices_identifier
    
    def connect_device(self,device_serial_number):
        if(self.connected == True):
            raise RuntimeError("Another spectrometer is already connected to this instance of the driver object. Disconnect it first.")
        self.list_devices()
        valid_serialnumbers = [dev[1] for dev in self.list_devices_identifier]
        try:
            ID_device = valid_serialnumbers.index(device_serial_number)
        except ValueError:
            raise ValueError("The specified serial number does not correspond to a valid device.")
        self.device = Spectrometer(self.list_spectrometers[ID_device])
        try:
            self.device.open()
            self.connected = True
            self.read_parameters_upon_connection()
            self.integration_time_microseconds = self._integration_time_microseconds
        except Exception as e:
            self.device = None
            self.connected = False
            raise RuntimeError("An error occurred while attempting connection to this device: " + str(e))
        return True

    def check_if_device_has_TEC(self):
        self.check_valid_connection()
        if hasattr(self.device._dev.f.thermo_electric,'enable_tec'):
            self.does_device_have_TEC = True
        else:
            self.does_device_have_TEC = False

    def read_parameters_upon_connection(self):
        self.check_if_device_has_TEC()
        if self.does_device_have_TEC:
            self.TEC_Temperature
        self.integration_time_limits_microseconds

    def disconnect_device(self):
        self.check_valid_connection()
        try:
            self.device.close()
            self.device = None
            self.connected = False
        except Exception as e:
            raise RuntimeError("An error occurred while attempting to disconnect the device: " + str(e))
        return True

    def check_valid_connection(self):
        if not(self.connected):
            raise RuntimeError("No spectrometer is currently connected.")
        
    @property
    def wavelength_units(self):
        self.check_valid_connection()
        return 'nm'
    
    @property
    def wavelengths(self):
        self.check_valid_connection()
        self._wavelengths = self.device.wavelengths()
        return self._wavelengths

    @property
    def intensities(self):
        self.check_valid_connection()
        self._intensities = self.device.intensities()
        return self._intensities

    @property
    def spectrum(self):
        self.check_valid_connection()
        self._wavelengths = self.device.wavelengths()
        self._intensities = self.device.intensities()
        return self._wavelengths,self._intensities

    @property
    def TEC_Temperature(self):
        self.check_valid_connection()
        if self.does_device_have_TEC == False:
            raise RuntimeError("This device does not have a TEC.")
        self._TECtemperature = self.device._dev.f.thermo_electric.read_temperature_degrees_celsius()
        return self._TECtemperature 

    @TEC_Temperature.setter
    def TEC_Temperature(self,temperature):
        self.check_valid_connection()
        if self.does_device_have_TEC == False:
            raise RuntimeError("This device does not have a TEC.")
        try:
            temperature = float(temperature)
        except:
            raise TypeError("Temperature  must be a valid float number.")
        self.device._dev.f.thermo_electric.set_temperature_setpoint_degrees_celsius(temperature)
        return self._TECtemperature 

    @property
    def integration_time_limits_microseconds(self):
        self.check_valid_connection()
        self._integration_time_limits_microseconds = self.device.integration_time_micros_limits
        return self._integration_time_limits_microseconds

    @property
    def integration_time_microseconds(self):
        self.check_valid_connection()
        return self._integration_time_microseconds

    @integration_time_microseconds.setter
    def integration_time_microseconds(self,time):
        self.check_valid_connection()
        try:
            time = int(time)
        except:
            raise TypeError("Integration time must be a valid integer number")
        if time <=0:
            raise TypeError("Integration time must be a positive integer number")
        if (time < self._integration_time_limits_microseconds[0]) or (time > self._integration_time_limits_microseconds[1]):
            raise TypeError(f"Integration time must be between {self._integration_time_limits_microseconds[0]} and {self._integration_time_limits_microseconds[1]}")
        self.device.integration_time_micros(time)
        self._integration_time_microseconds = time
        return self._integration_time_microseconds
    
