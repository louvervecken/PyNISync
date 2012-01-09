from ctypes import *

# New types definitions
# Correspondance between the name used in the niSync.h file and ctypes
ViUInt16 = c_ushort
ViInt16 = c_short
ViUInt32 = c_ulong
ViInt32 = c_long
ViConstString = c_char_p
ViRsrc = c_char_p
ViReal64 = c_double

ViBoolean = ViUInt16
ViSession = ViUInt32
ViStatus = ViInt32
ViAttr = ViUInt32