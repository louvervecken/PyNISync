import re
import sys
from ctypes import *
from .SyncConfig import dot_h_file, lib_name
from .SyncTypes import *

class SyncError(Exception):
    """Exception raised from the NISYNC.

    Attributes:
        error -- Error number from NI
        message -- explanation of the error
    """
    def __init__(self, error, mess, fname):
        self.error = error
        self.mess = mess
        self.fname = fname
    def __str__(self):
        return self.mess + '\n in function '+self.fname

def catch_error(f):
    def mafunction(*arg):
        error = f(*arg)
        if error<0:
            errBuff = create_string_buffer(256)
            error_message( 0, error, errBuff)
            raise SyncError(error,errBuff.value.decode("utf-8"), f.__name__)
        elif error>0:
            errBuff = create_string_buffer(256)
            error_message ( 0, error, errBuff);
            print("WARNING  :",error, "  ", errBuff.value.decode("utf-8"))
            raise SyncError(error,errBuff.value.decode("utf-8"))

        return error
    return mafunction
if sys.platform.startswith('win'):        
    Synclib = windll.LoadLibrary(lib_name)
elif sys.platform.startswith('linux'):
    Synclib = cdll.LoadLibrary(lib_name)
# else other platforms will already have barfed importing SyncConfig

######################################
# Array
######################################
#Depending whether numpy is install or not, 
#the function array_type is defined to return a numpy array or
#a ctype POINTER
try:
    import numpy
except ImportError:
    def array_type(string):
        return eval('POINTER('+string+')')
else:
    # Type conversion for numpy
    def numpy_conversion(string):
        """ Convert a type given by a string to a numpy type

        """
        #This function uses the fact that the name are the same name, 
        #except that numpy uses lower case
        return eval('numpy.'+string.lower())
    def array_type(string):
        """ Returns the array type required by ctypes when numpy is used """
        return numpy.ctypeslib.ndpointer(dtype = numpy_conversion(string))

################################
#Read the .h file and convert the function for python
################################
include_file = open(dot_h_file,'r') #Open niSync.h file

################################
# Regular expression to parse the niSync.h file
# Almost all the function define in niSync.h file are imported
################################

# Each regular expression is assiciated with a ctypes type and a number giving the 
# group in which the name of the variable is defined


#fonction_parser = re.compile(r'.* (niSync_\S+)\s*\(((.|\r|\n)*)\);')
fonction_parser = re.compile(r'.* niSync_(\S+)\s*\((.*)((\);)|(,\Z))')
function_parser_arguments = re.compile(r'\s*(.*?)(,*)(\);)*\Z')

type_list = ['ViUInt16','ViInt16','ViUInt32','ViInt32','ViConstString','ViRsrc','ViReal64','ViBoolean','ViSession','ViStatus','ViAttr']

# Each regular expression is assAciated with a ctypes type and a number giving the 
# group in which the name of the variable is defined
simple_type = [(re.compile('('+_type+')\s*([^\*\[]*)\Z'),eval(_type),2)
     for _type in type_list]
pointer_type = [(re.compile('('+_type+')\s*\*([^\*]*)\Z'),
        eval('POINTER('+_type+')'),2) for _type in type_list]

char_array = [(re.compile(r'(ViChar)\s*([^\s]*)\[\d*\]'), c_char_p,2)] # match "ViChar name[]" and ViChar name[256]


# Create a list with all regular expressions
c_to_ctype_map = []
for l in [simple_type, pointer_type, char_array]:
    c_to_ctype_map.extend(l)



# The list of all function 
# function_dict: the keys are function name, the value is a dictionnary 
# with 'arg_type' and 'arg_name', the type and name of each argument 
function_list = [] 
function_dict = {} 


def _define_function(name, arg_list, arg_name):
    # Record details of function
    function_dict[name] = {'arg_type':arg_list, 'arg_name':arg_name}
    # Fetch C function and apply argument checks
    cfunc = getattr(Synclib, "niSync_" + name)
    setattr(cfunc, 'argtypes', arg_list)
    # Create error-raising wrapper for C function and add to module's dict
    func = catch_error(cfunc)
    func.__name__ = name
    typeAndName=[]
    for type_i, name_i in zip(arg_list, arg_name):
        typeAndName.append(str(type_i).replace("class ", "") + ' ' + name_i)
    func.__doc__ = '%s(%s) -> error.' % (name, ','.join(typeAndName))
    globals()[name] = func


arg_string = ''
functionContinuesOnNextLine = False

for line in include_file:
    functionParsed = False
    line = line[0:-1]
    
    if '_VI_FUNC' in line and fonction_parser.match(line):
        name = fonction_parser.match(line).group(1)
        function_list.append(name)
        arg_string = fonction_parser.match(line).group(2)
        #if goup 3 is a ',' then it means the function declaration continues on the next line
        if ',' in fonction_parser.match(line).group(3):
            functionContinuesOnNextLine = True
            continue
        elif ');' in fonction_parser.match(line).group(3):
            functionContinuesOnNextLine = False
            functionParsed = True
        else:
            print("Error parsing function " + name)

    if function_parser_arguments.match(line) and functionContinuesOnNextLine:
        arg_string = arg_string + ', ' + function_parser_arguments.match(line).group(1)
        if ',' in function_parser_arguments.match(line).group(2):
            functionContinuesOnNextLine = True
            continue
        else:
            functionContinuesOnNextLine = False
            functionParsed = True
       
    if functionParsed:
        arg_list=[]
        arg_name = []
        for arg in re.split(', ',arg_string):
            for (reg_expr, new_type, groug_nb) in c_to_ctype_map:
                reg_expr_result = reg_expr.search(arg)
                if reg_expr_result is not None:
                    arg_list.append(new_type)
                    arg_name.append(reg_expr_result.group(groug_nb))
                    break # break the for loop
            else:
                print("could not parse " + arg + "in function " + name)
        _define_function(name, arg_list, arg_name)

include_file.close()




# Clean private functions from namespace
del _define_function
