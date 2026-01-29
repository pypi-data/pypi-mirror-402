# randstadenterprise_edao_libraries/logs.py
import threading
from datetime import datetime
from typing import List, Any, Optional

def log (inst_url: str, msg: str, logs_array: List[List[Any]], lock: threading.Lock, print_to_console: bool = False):
    # =======================================================================
    # LOGS A MESSAGE TO A SHARED ARRAY IN A THREAD-SAFE MANNER
    # =======================================================================
        
    if print_to_console:

        inst_url_length = len(inst_url)

        if inst_url_length <= 10:
            tabs = "\t\t\t\t\t"
        elif inst_url_length <= 15:
            tabs = "\t\t\t\t\t"
        elif inst_url_length <= 22:
            tabs = "\t\t\t\t"
        elif inst_url_length <= 26:
            tabs = "\t\t\t"
        elif inst_url_length <= 30:
            tabs = "\t\t\t"
        elif inst_url_length <= 35:
            tabs = "\t\t"
        elif inst_url_length < 39:
            tabs = "\t\t"
        else:
            tabs = "\t"

        print(f"#{inst_url}{tabs}{msg}")

    # END if self.PRINT_TO_CONSOLE:

    with lock: # <--- Must be 'lock' (or whatever name is used in the lambda)
        # START with lock
        logs_array.append([inst_url, msg, datetime.now()]) 
    # END with lock
# END def log

############################
# PRINT RESPONSE
############################
def print_response(inst_url: str, msg: str, resp: Any, 
                   logs_array: Optional[List[List[Any]]] = None, 
                   lock: Optional[threading.Lock] = None):

    # 1. Safely get the reason (handle mock objects or real responses)
    reason = resp.reason if getattr(resp, "reason", None) else "RESPONSE DOES NOT HAVE A REASON"
    
    # 2. Construct the formatted string
    full_message = f"{msg}: {str(resp)} : {str(reason)}"

    # 3. Always print to console (Original behavior)
    print(f"{inst_url}: {full_message}")

    # 4. If logging tools are provided, append to the array (New behavior for Test)
    if logs_array is not None and lock is not None:
        # Reuse your existing log function to handle timestamps/locking automatically
        log(inst_url, full_message, logs_array, lock)
        
# END def print_response(inst_url, msg, resp): 

# In logs.py
        