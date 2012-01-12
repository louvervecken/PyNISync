from .SyncTypes import ViSession
from . import SyncFunctions
from .SyncFunctions import *
#from .SyncCallBack import *

# Create a list of the name of the function that uses ViSession as the firs argument
# All the function of this list will be converted to method of the Session object
# The name of the method will be the same name as the name of the niSync function without the 
# the niSync in front of the name
session_function_list = [name for name in list(function_dict.keys()) if \
                 len(function_dict[name]['arg_type'])>0 and \
                 (function_dict[name]['arg_type'][0] is ViSession) and\
                 'vi' in function_dict[name]['arg_name'][0]]


class Session():
    def __init__(self, resourceName, resetDevice=False):
        sessionID = ViSession(0)
        # get the session id, the idQuery is ignored and set to True here
        niSync_init(resourceName.encode('latin-1'), True, resetDevice, byref(sessionID))
        self.sessionID = sessionID
        self.__cleared = False #Flag to clear the session only once
    def __del__(self):
        """ Clear automatically the session to be able to reallocate resources """ 
        # Clear the session before deleting the object
        # If the session as already been manually cleared, nothing is done
        # This prevent to clear a session that has a Handle attributes to a new session
        # See this example
        # a = Session(), ..., a.ClearSession(), b = Session(), del(a)
        # b has the same sessionID as a, and deleting a will clear the session of b   
        try: 
            if not self.__cleared:
                self.ClearSession()
        except SyncError:
            pass
    def ClearSession(self):
        niSync_close(self.sessionID)
        self.__cleared = True
    def __repr__(self):
        return "Session number %d"%self.sessionID.value


# Remove niSync_close in task_functon_list
session_function_list = [name for name in session_function_list if name not in ['niSync_close']]

def _create_method(func):
    def _call_method(self,*args):
        return func(self.sessionID, *args)
    return _call_method


for function_name in session_function_list:
    name = function_name[7:] # remove the niSync_ in front of the name
    func = getattr(SyncFunctions, function_name)
    arg_names = function_dict[function_name]['arg_name']
    sessionfunc = _create_method(func)
    sessionfunc.__name__ = name
    sessionfunc.__doc__ = 'T.%s(%s) -> error.' % \
            (name, ', '.join(arg_names[1:]))
    setattr(Session, name, sessionfunc)

# Clean private functions from namespace
del _create_method
