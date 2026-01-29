
- Check list of devices that are supported by seabreeze
- If your device is supported by cseabreeze, then no other step is required
- If your device is supported only via pyseabreeze, then you need to do the following
    - Set up pyOceanOpticsSpectrometer so that it uses pyseabreeze
    - Install pip install pyusb
    - Install pip install libusb
    - You might need to manually add a .dll file to your system. Go here https://libusb.info/, Downloads -> Latest Windows Binaries. In the zip file, enter either the folder MinGW64/dll or MinGW32/dll (depending on your OS). Copy the file  libusb-1.0.dll into C:\Windows\System32