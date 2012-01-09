import sys
import platform

if sys.platform.startswith('win'):
    # Full path of the niSync.h file
    # Default location on Windows XP
    dot_h_file = r'C:\Program Files\IVI Foundation\VISA\WinNT\include\niSync.h'

    if platform.release()=='7':
        dot_h_file = r'C:\Program Files (x86)\IVI Foundation\VISA\WinNT\include\niSync.h'

    # Name (and eventually path) of the library
    # Default on Windows is nicaiu
    lib_name = "nicaiu"

elif sys.platform.startswith('linux'):
    # On linux you can use the command find_library('nidaqmx')

    # Full path of the NIDAQmx.h file
    dot_h_file = '/usr/local/natinst/nidaqmx/include/NIDAQmx.h'

    # Name (and eventually path) of the library
    lib_name = 'libnidaqmx.so'

else:
    raise NotImplementedError("Location of niDAQmx library and include file unknown on %s - if you find out, please let the PyDAQmx project know" % (sys.platform))
