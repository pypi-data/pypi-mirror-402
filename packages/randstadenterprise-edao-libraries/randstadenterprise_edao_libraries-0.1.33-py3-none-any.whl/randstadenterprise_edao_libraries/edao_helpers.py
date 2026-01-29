# randstadenterprise_edao_libraries/helpers.py
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field 
from datetime import datetime
from typing import Optional, Any, Callable
import logging

import domojupyter as domo
from pydomo import Domo

# Define the type for the log function for clean type hinting
LogFunc = Callable[[str], None] 

# =======================================================================
# CORE HELPER FUNCTIONS
# =======================================================================

############################
# INIT DOMO SDK CLIENT
    # - Create an API client on https://developer.domo.com
    # - Initialize the Domo SDK with your API client id/secret
    # - If you have multiple API clients you would like to use, simply initialize multiple Domo() instances
    # - Docs: https://developer.domo.com/docs/domo-apis/getting-started
############################
def init_domo_client(inst_url, client_id, client_secret):

    api_url = inst_url + '.domo.com'

    return Domo(client_id, client_secret, api_host='api.domo.com')

# END init_domo_client():    
    
# =======================================================================
# RETURNS THE CURRENT DATETIME OBJECT
# """Returns the current datetime object."""    
# =======================================================================
def get_current_time () -> datetime:
    return datetime.now()
# END def get_current_time

def dataframe_to_csv (dataframe: pd.DataFrame) -> str:
# =======================================================================
# CONVERTS A PANDAS DATAFRAME TO CSV STRING
# =======================================================================
    # START def dataframe_to_csv
    """
    Converts a pandas DataFrame into a CSV string (without header/index).
    
    :param dataframe: The pandas DataFrame to convert.
    :returns: The resulting CSV data as a string.
    """
    return dataframe.to_csv(header=False, index=False)
# END def dataframe_to_csv

def array_to_csv (array: List[List[Any]], cols: List[str]) -> str:
# =======================================================================
# CONVERTS A 2D LIST ARRAY TO CSV STRING VIA DATAFRAME
# =======================================================================
    # START def array_to_csv
    """
    Converts a list of lists (array) into a CSV string (without header/index).
    
    :param array: The 2D list of data.
    :param cols: The list of column names.
    :returns: The resulting CSV data as a string.
    """
    # 1. Convert list of lists to DataFrame
    dataframe = pd.DataFrame(array, columns=cols)
    # 2. Convert DataFrame to CSV string
    return dataframe_to_csv(dataframe)
# END def array_to_csv

def load_instance_map (inst_df: pd.DataFrame) -> Dict[str, Any]:
# =======================================================================
# LOADS INSTANCE CONFIGURATIONS FROM DATAFRAME
# =======================================================================
    """
    Parses a DataFrame containing Domo instance configurations and returns a 
    dictionary mapping instance URL to a typed Instance object.
    
    :param inst_df: The pandas DataFrame containing instance configurations.
    :returns: A dictionary mapping {Instance_URL (str): objects.Instance (object)}.
    """
    
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    instance_map: Dict[str, domo_objects.Instance] = {}
    
    # Get the fields from the objects.Instance dataclass
    instance_fields = [f.name for f in domo_objects.Instance.__dataclass_fields__.values()]
    
    # 1. Map DataFrame column names to Instance object field names
    for i in inst_df.index:
        # START for i in inst_df.index
        
        # Build arguments dynamically, defaulting to None if column is missing
        kwargs = {}
        for field_name in instance_fields:
            # Convert snake_case field name to Title Case column name (e.g., Instance_URL -> Instance URL)
            df_col_name = field_name.replace('_', ' ')
            
            # Use .get with default list to handle potentially missing columns safely
            value = inst_df.get(df_col_name, [None] * len(inst_df))[i]
            
            # Clean and store the value
            if field_name == 'Order' and value is not None and pd.notna(value):
                # Handle integer conversion for 'Order'
                kwargs[field_name] = int(value)
            elif value is not None and pd.notna(value):
                # All other fields are treated as strings
                kwargs[field_name] = str(value)
            else:
                kwargs[field_name] = None
        
        inst_url = kwargs.get('Instance_URL', str(i))
        
        # 2. Create the Instance object using collected keyword arguments
        instance_obj = domo_objects.Instance(**kwargs)
        
        # 3. Map instance object using Instance URL as the key
        instance_map[inst_url] = instance_obj
        # END for i in inst_df.index
        
    return instance_map
# END def load_instance_map

# =======================================================================
# Retrieves the specified Domo Account Property from the Domo Account Properties
# This method is so that the retireval is not hardcoded to the [1] index
# =======================================================================
def get_domo_account_property (log_func: LogFunc, instance: str, prop_key:str) -> Optional[str]:
    
    # 1. Get the list of available property keys
    account_prop_keys = domo.get_account_property_keys(instance)
    
    # 2. Discovery: Check if the requested property exists in the array
    if prop_key in account_prop_keys:
        # Find the specific index of the key (satisfying the discovery requirement)
        key_index = account_prop_keys.index(prop_key)
        target_key = account_prop_keys[key_index]
        
        # log_func(f"Property '{prop_key}' found at index {key_index}.")
        
        # 3. Retrieve the value using the discovered key
        prop_value = domo.get_account_property_value(instance, target_key)
        
        # logging the value length for security instead of the full token
        # val_len = len(str(prop_value)) if prop_value else 0
        # log_func(f"Retrieved value for '{target_key}' (Length: {val_len})")
        
        return prop_value
        
    else:
        log_func(f"ERROR: Property '{prop_key}' not found in account properties: {account_prop_keys}")
        return None        
    
# END def get_domo_account_property