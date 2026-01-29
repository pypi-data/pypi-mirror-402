# randstadenterprise_edao_libraries/datasets.py
from typing import List, Dict, Any, Optional, Callable, Union
from pydomo.datasets import DataSetRequest, Schema, Column
from pydomo import Domo
import datetime as datetime

# Define custom types needed for function signatures
LogFunc = Callable[[str], None]

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# DATASET RETRIEVAL AND LOOKUP

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# =======================================================================
# RETRIEVES ALL DATASETS VIA PYDOMO SDK PAGINATION
#     Retrieves ALL datasets from a Domo instance by handling full pagination 
#     of the PyDomo SDK's list() method.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token (included for consistency, but unused here).
#     :param domo_ds_api: The PyDomo datasets client object.
#     :param inst_name: The instance name (for logging context).
#     :param lock: The threading.Lock object (for logging).
#     :param logs_array: The shared log array.
#     :param page_size: The number of results per page (defaults to 100).
#     :returns: A list containing all objects.Dataset objects.
# =======================================================================
def get_instance_datasets (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc) -> List[Any]:
    
    log_func(f"____ get_instance_datasets: {inst_url}")
    
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_helpers 
    from . import domo_objects 

    
    stats = get_instance_dataset_stats(inst_url, inst_dev_token, domo_ds_api, log_func)
    
    dataset_count = 1000
    if "numDatasources" in stats:
        dataset_count = stats["numDatasources"]
        log_func(f"____ dataset_count: {str(dataset_count)}")
    # END if numDatasources in stats:

    all_datasets_raw = []
    if dataset_count > 1000:
        all_datasets_raw = _get_datasets_by_years(inst_url, inst_dev_token, log_func)      
    else:
        start_date = datetime.datetime(2000, 1, 1, 0, 0, 0)
        end_date = datetime.datetime(edao_helpers.get_current_time().year, 12, 31, 23, 59, 59)
        all_datasets_raw = _get_datasets_by_date_range(inst_url, inst_dev_token, log_func, start_date, end_date)
    # END if dataset_count > 500:
    
    all_datasets_objects: List[domo_objects.Dataset] = []
    all_datasets_objects = _load_dataset_objects(log_func, all_datasets_raw)

    # for ds in all_datasets_raw:
    #     dataset_object = _load_dataset_object(ds, log_func)
    #     all_datasets_objects.append(dataset_object)            
    # # END for ds in all_datasets_raw
        
    log_func(f"____ END get_instance_datasets: {inst_url}")
    
    return all_datasets_objects

# END def get_all_instance_datasets

# =======================================================================
# SEARCHES FOR AN EXACT DATASET MATCH BY NAME
#     Searches for a dataset by id using the Domo UI Search API (wildcard) 
#     and returns the exact match.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param dataset_id: The exact name of the dataset to find.
#     :returns: The objects.Dataset object if found, otherwise None.
# =======================================================================
def get_dataset_by_id (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, dataset_id: str) -> Any:

    log_func(f"____ get_dataset_by_id({dataset_id})")

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 
    
    api_url = f"https://{inst_url}.domo.com/api/data/v3/datasources/{dataset_id}?includeAllDetails=true&includePrivate=true"

    resp = edao_http.get(api_url, inst_dev_token, log_func)

    dataset_object = _load_dataset_object(resp, log_func)
    
    log_func(f"____ END get_dataset_by_id({dataset_id})")
    
    return dataset_object
# END def get_dataset_by_id

# =======================================================================
# SEARCHES FOR AN EXACT DATASET MATCH BY NAME
# Searches for a dataset by name using the Domo UI Search API (wildcard) 
#     and returns the exact match.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param dataset_name: The exact name of the dataset to find.
#     :param log_func: Pre-bound logging function.
#     :returns: The objects.Dataset object if found, otherwise None.
# =======================================================================
def get_dataset_by_name (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, dataset_name: str) -> Any:
    
    log_func(f"____ get_dataset_by_name({dataset_name})")

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f'https://{inst_url}.domo.com/api/data/ui/v3/datasources/search'
    # headers = helpers.get_http_headers(inst_dev_token)

    body = {
        "entities": ["DATASET"],
        "filters": [{"field": "name_sort", "filterType": "wildcard", "query": f"*{dataset_name}*"}],
        "combineResults": "true",
        "query": "*",
        "count": 30, 
        "offset": 0,
        "sort": {"isRelevance": "false", "fieldSorts": [{"field": "create_date", "sortOrder": "DESC"}]}
    }
    
    resp = edao_http.post(api_url, inst_dev_token, log_func, body)

    dataset_json = None

    # Iterate through results to find the exact name match
    if "dataSources" in resp:
        for ds in resp["dataSources"]: 
            # START for ds in datasets_json["dataSources"]
            if ds.get("name") == dataset_name:
                # START if ds.get("name") == dataset_name
                dataset_json = ds
                break
            # END if ds.get("name") == dataset_name
        # END for ds in datasets_json["dataSources"]
    # END if "dataSources" in datasets_json
    
    dataset_object = _load_dataset_object (dataset_json, log_func)
    
    log_func(f"____ END get_dataset_by_name({dataset_name})")
    return dataset_object

# END def get_dataset_by_name

# =======================================================================
# RETRIEVES INSTANCE HIGH-LEVEL DATASET STATISTICS

#     Retrieves high-level customer stats (like total dataset count) for an instance.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param domo_ds_api: Domo dataset library.
#     :param log_func: Pre-bound logging function.
#     :returns: Dictionary containing instance stats, or raises an HTTPError.

# =======================================================================
def get_instance_dataset_stats (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc) -> Dict[str, Any]:
    
    log_func(f"____ get_instance_dataset_stats({inst_url})")
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/query/v1/datasources/customer-stats'

    resp = edao_http.get(api_url, inst_dev_token, log_func)
    log_func(f"____ END get_instance_dataset_stats({inst_url})")
    return resp
# END def get_instance_dataset_stats

# =======================================================================
# RETRIEVES USER/GROUP PERMISSIONS FOR A DATASET
#     Retrieves all user/group permissions for a given dataset ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param ds_id: The ID of the dataset.
#     :param log_func: Pre-bound logging function.
#     :returns: Map of {Permission_Name (original case): Permission_Details}, or None on critical failure.
# =======================================================================
def get_dataset_permissions (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, ds_id: str) -> Optional[Dict[str, dict]]:

    log_func(f'____ get_dataset_permissions({inst_url}, {ds_id})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f'https://{inst_url}.domo.com/api/data/v3/datasources/{ds_id}/permissions'
    
    dataset_perms_map: Dict[str, dict] = {}
    
    permissions_json = edao_http.get(api_url, inst_dev_token, log_func)

    if "list" in permissions_json and isinstance(permissions_json["list"], list):
        for perm_entry in permissions_json["list"]:
            if isinstance(perm_entry, dict) and "name" in perm_entry:
                dataset_perms_map[perm_entry["name"]] = perm_entry
            # END if isinstance(perm_entry, dict) and "name" in perm_entry
        # END for perm_entry in permissions_json["list"]
    # END if "list" in permissions_json and isinstance(permissions_json["list"], list)
    else:
        log_func(f"_____ WARN (DS_ID: {ds_id}): 'list' key not found or not a list in permissions response.")
    # END else

    log_func(f'____ get_dataset_permissions({inst_url}, {ds_id})')
    return dataset_perms_map
        
# END def get_dataset_permissions


# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# DATASET MODIFICATION/ACTION FUNCTIONS

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================


# =======================================================================
# CREATES A DATASET AND IMPORTS DATA
# =======================================================================
def create_dataset (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, dataset_name: str, dataset_description: str, dataset_cols: List[Column], dataset_array: List[List[Any]]) -> Optional[Any]:
    
    log_func(f"____ create_dataset({dataset_name}, {dataset_description})")
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    from . import edao_helpers 
    from . import domo_objects

    new_dataset_id = None

    # 1. Create Dataset with schema
    log_func(f"_______ Attempting to CREATE new dataset: {dataset_name}")
    try:
        # START try
        # Create the dataset request and call the PyDomo create method
        dsr = DataSetRequest(name=dataset_name, description=dataset_description, schema=Schema(dataset_cols))
        dataset = domo_ds_api.datasets.create(dsr)
        new_dataset_id = dataset['id']
        log_func(f"_______ Dataset CREATED with ID: {new_dataset_id}")
    # END try
    except Exception as e:
        # START except Exception as e
        log_func(f"_______ CRITICAL ERROR creating dataset {dataset_name}: {e}")
        return None
        # END except Exception as e
    
    # 2. Import Data
    if new_dataset_id and dataset_array:
        # Convert data array to CSV string
        # --- Transformation Code ---
        
        dataset_cols = [col.name for col in dataset_cols]
        
        dataset_csv = edao_helpers.array_to_csv(dataset_array, dataset_cols)
        try:
            # Import data via PyDomo
            domo_ds_api.datasets.data_import(new_dataset_id, dataset_csv)
            log_func(f"_______ SUCCESS: Data import to {dataset_name}.")
        # END try
        except Exception as e:
            log_func(f"_______ ERROR: Data import failed for {dataset_name}. Exception: {e}")
        # END except Exception as e
    # END if current_dataset_id and dataset_array
    
    # Create the Dataset object
    dataset_object = domo_objects.Dataset(
        id=new_dataset_id,
        name=dataset_name,
        description=dataset_description
    )
            
    log_func("____ END create_dataset()")
    
    return dataset_object
# END def create_dataset

# =======================================================================
# SAVES (CREATES OR UPDATES) A DATASET
    # :param inst_url: The Domo instance URL prefix.
    # :param inst_dev_token: The developer token.
    # :param domo_ds_api: The PyDomo datasets client object.
    # :param dataset_obj: The objects.Dataset object (dataclass instance) to be saved.
    # :param log_func: Pre-bound logging function.
    # :returns: The string ID of the saved dataset, or None on failure.
# =======================================================================
def save_dataset (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, dataset_obj: Any) -> Optional[str]:

    log_func(f'____ save_dataset({str(inst_url)}, {dataset_obj.name})')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    body = {"dataSourceName":dataset_obj.name,"dataSourceDescription":dataset_obj.description}
    
    api_url = f"https://{inst_url}.domo.com/api/data/v3/datasources/{dataset_obj.id}/properties"
    
    resp = edao_http.put(api_url, inst_dev_token, log_func, body)

    log_func(f'____ END save_dataset({str(inst_url)}, {dataset_obj.name})')

    return dataset_obj.id

# END def save_dataset

# =======================================================================
# DELETES A DATASET BY ID
    # :param inst_url: The Domo instance URL prefix.
    # :param inst_dev_token: The developer token.
    # :param log_func: Pre-bound logging function.
    # :param dataset_id: The string ID of the dataset to delete.
    # :returns: True on success, False on failure.
# =======================================================================
def delete_dataset (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, dataset_id: str) -> bool:
    
    log_func(f"____ delete_dataset({str(inst_url)}, {str(dataset_id)}")
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f"https://{inst_url}.domo.com/api/data/v3/datasources/{dataset_id}?deleteMethod=soft"
    
    resp = edao_http.delete(api_url, inst_dev_token, log_func)
    
    log_func(f"____ END delete_dataset({str(inst_url)}, {str(dataset_id)}")
    return True

# END def delete_dataset

# =======================================================================
# SHARES A DATASET WITH A USER OR GROUP
#     Shares a dataset with a user or group.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param ds_id: The ID of the dataset to share.
#     :param share_type: The type of entity being shared with ('USER' or 'GROUP').
#     :param share_id: The ID of the user or group.
#     :param share_name: The display name of the user or group.
#     :param access_lvl: The access level ('CO_OWNER', 'CAN_EDIT', 'CAN_SHARE').
#     :param log_func: Pre-bound logging function.
#     :returns: True on success, False on failure.
# =======================================================================
def share_dataset(inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, ds_id: str, share_type: str, share_id: int, share_name: str, access_lvl: str) -> bool:

    log_func(f'____ share_dataset({inst_url}, {ds_id}, {share_type}, {share_id}, {access_lvl}')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f'https://{inst_url}.domo.com/api/data/v3/datasources/{ds_id}/permissions'

    # 1. Lookup access level details
    lbl_desc_lookup = {
        "CO_OWNER": {"label": "Co-owner", "description": "Allows for editing and deleting DataSet (same as owner)"},
        "CAN_EDIT": {"label": "Can Edit", "description": "Allows for editing and sharing DataSet, but can't delete"},
        "CAN_SHARE": {"label": "Can Share", "description": "Allows for sharing, but can't edit DataSet at all"}
    }
    
    if access_lvl not in lbl_desc_lookup:
        # START if access_lvl not in lbl_desc_lookup
        log_func(f"ERROR (DS_ID: {ds_id}): Invalid access_lvl '{access_lvl}' in share_dataset.")
        return False
        # END if access_lvl not in lbl_desc_lookup

    access_details = lbl_desc_lookup[access_lvl]
    
    # 2. Define API body
    body = {
        "accessLevel": access_lvl,
        "accessObject": {
            "accessLevel": access_lvl,
            "label": access_details["label"],
            "description": access_details["description"]
        },
        "id": share_id, 
        "name": share_name,
        "type": share_type
    }

    resp = edao_http.put(api_url, inst_dev_token, log_func, body)
    return True

    log_func(f'____ END share_dataset({inst_url}, {ds_id}, {share_type}, {share_id}, {access_lvl}')

# END def share_dataset

# =======================================================================
# UNSHARES A DATASET FROM A USER OR GROUP
#     Unshares a dataset with a user or group.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param ds_id: The ID of the dataset.
#     :param share_type: The type of entity being unshared from ('USER' or 'GROUP').
#     :param share_id: The ID of the user or group.
#     :param log_func: Pre-bound logging function.
#     :returns: True on success or if permission is already gone (404), False on other failures.
# =======================================================================
def unshare_dataset (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, ds_id: str, share_type: str, share_id: str) -> bool:

    log_func(f'____ unshare_dataset({inst_url}, {ds_id}, {share_type}, {share_id}')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f'https://{inst_url}.domo.com/api/data/v3/datasources/{ds_id}/permissions/{share_type}/{share_id}'

    resp = edao_http.delete(api_url, inst_dev_token, log_func)

    return True
    
    log_func(f'____ END unshare_dataset({inst_url}, {ds_id}, {share_type}, {share_id}')
    
# END def unshare_dataset

# =======================================================================
# SAVE DATASET AI CONTEXT
#     save a dataset ai context
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param dataset_id: The ID of the dataset.
#     :param log_func: Pre-bound logging function.
#     :param ai_context: json formatted context

#     :returns: True on success or if permission is already gone (404), False on other failures.
# =======================================================================
def save_dataset_ai_context (inst_url: str, inst_dev_token: str, domo_ds_api: Any, log_func: LogFunc, dataset_obj: Any, ai_context: Any) -> bool:

    log_func(f'____ save_dataset_ai_context({inst_url}, {dataset_obj.id}')    
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    data_dictionary_object = _get_data_dictionary(inst_url, inst_dev_token, log_func, dataset_obj.id)
    
    data_dict_id =  dataset_obj.id

    api_url = f"https://{str(inst_url)}.domo.com/api/ai/readiness/v1/data-dictionary/dataset/{str(dataset_obj.id)}"

    body = {
        "id":  dataset_obj.id,
        "datasetId": dataset_obj.id,
        "name": dataset_obj.name + " dictionary",
        "description": dataset_obj.description,
        "unitOfAnalysis": "",
        "columns": []
    }

    if not data_dictionary_object:
        
        resp = edao_http.post(api_url, inst_dev_token, log_func, body)
        
        data_dict = resp.get("dataDictionary", {})
        
        data_dict_id = data_dict["id"]
        
    # if !data_dictionary_object:


    columns_payload = []
    for field in ai_context.get('fields', []):
        columns_payload.append({
            "name": field.get('field_name', '').lower(),
            # "name": field.get('field_name', '').replace('_', ' ').lower(),
            "description": field.get('description', ''),
            "synonyms": field.get('synonyms', []),
            "subType": None,
            "agentEnabled": True,
            "beastmodeId": None,
            "sampleValues": field.get('example_values', ""),
        })
    # END for field in data_dictionary_content.get('columns', []):

    body["id"] = data_dict_id
    body["columns"] = columns_payload

    # log_func(f'_______ BODY : {str(body)}')

    resp = edao_http.put(api_url, inst_dev_token, log_func, body)
    
    return True
    
    log_func(f'____ END save_dataset_ai_context({inst_url}, {dataset_obj.id}')
    
# END def save_dataset_ai_context

# =======================================================================
# GET DATA DICTIONARY
# Looks up a dataset DataDictionary Id by its name using the Domo search API.

#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param dataset_id: The ID of the dataset.

# Returns:
#     str | None: The ID of the dataset if found, otherwise None.
# =======================================================================

def _get_data_dictionary (inst_url: str, inst_dev_token: str, log_func: LogFunc, dataset_id: str):

    log_func(f'____ _get_data_dictionary({inst_url}, {dataset_id}')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    url = f"https://{inst_url}.domo.com/api/ai/readiness/v1/data-dictionary/dataset/{dataset_id}"

    # print(f"_______ GET DATA DICTIONARY URL: {str(url)}")
    resp = edao_http.get(url, inst_dev_token, log_func)
    
    # logs.print_response(inst_url, f"_get_data_dictionary: ", resp)

    data_dictionary_object = None
    
    if resp:
        
        result = resp.json()
        print(f"_______ GET DATA DICTIONARY JSON: {str(result)}")
        if result and len(result) > 0:
            # Assuming the first result is the correct one.
            dd = result[0]
            data_dict = dd.get("dataDictionary", {})

            data_dictionary_object = _load_datadictionary_object (data_dict, log_func)

        # END if result and len(result) > 0:              
        
    # END if resp:

    log_func(f'____ END _get_data_dictionary({inst_url}, {dataset_id}')

    return data_dictionary_object

# END def _get_data_dictionary():

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# PRIVATE API HELPER FUNCTIONS

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# =======================================================================
# PRIVATE: LOAD DATASET OBJECTS
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param datasets_json: json array of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
# def _load_dataset_objects (log_func: LogFunc, json_array: Any) -> List[objects.SandboxPromotionLog]:
    
#     objects = []    
#     if json_array:
#         for json in json_array:
#             obj = _load_dataset_object (log_func, json)            
#             objects.add(obj)
#         # END for dataset_json in datasets_json:

#     # END if dataset_json

#     return objects
# # END def _load_dataset_objects


def _load_dataset_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of objects.Dataset instances.
    Skips individual objects that fail to load.
    """
    loaded_objects = [] # Renamed from 'objects' to avoid shadowing the module name
    
    # 1. Validate the input array
    if json_array is None:
        log_func("WARN: Input json_array is None. Returning empty list.")
        return []
        
    if not isinstance(json_array, list):
        msg = f"CRITICAL: Input json_array must be a list, got {type(json_array).__name__}."
        log_func(msg)
        raise TypeError(msg)

    # 2. Iterate through the array
    for i, json_item in enumerate(json_array):
        try:
            # 3. Load individual object
            obj = _load_dataset_object(log_func, json_item)
            
            # Use .append() for Python lists (not .add)
            loaded_objects.append(obj)
            
        except (ValueError, RuntimeError) as e:
            # 4. Handle known errors from the single object loader
            log_func(f"ERROR: Failed to load object at index {i}. Skipping. Details: {e}")
            continue
            
        except Exception as e:
            # 5. Handle unexpected errors
            log_func(f"CRITICAL: Unexpected error loading object at index {i}: {e}")
            continue

    return loaded_objects
# END def _load_dataset_objects

# =======================================================================
# PRIVATE: LOAD DATASET OBJECT
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param dataset_json: json of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
# def _load_dataset_object (log_func: LogFunc, json: Any) -> objects.Dataset:

#     if json:
#         # START if datasets_search_results
#         return objects.Dataset(
#             id=json.get('id', ''),
#             name=json.get('name', ''),
#             data_provider_name=json.get('type'),
#             description=json.get('description'),
#             row_count=json.get('rowCount'),
#             column_count=json.get('columnCount'),
#             owners=[] # Ownership data often requires separate API call, stubbing for now
#         )
#     # END if dataset_json

# # END def _load_dataset_object

def _load_dataset_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an objects.Dataset instance. 
    Raises an error if JSON is missing or if object creation fails.
    """
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_dataset_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the Dataset object
        return domo_objects.Dataset(
            id=json.get('id', ''),
            name=json.get('name', ''),
            data_provider_name=json.get('type'),
            description=json.get('description'),
            row_count=json.get('rowCount'),
            column_count=json.get('columnCount'),
            owners=[] # Ownership data often requires separate API call, stubbing for now
        )
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate objects.Dataset. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_dataset_object(log_func: LogFunc, json: Any) -> objects.Dataset:        

# =======================================================================
# PRIVATE: LOAD DATA DICTIONARY OBJECT
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param dataset_json: json of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_datadictionary_object (data_dictionary_json: Any, log_func: LogFunc) -> Optional[Any]:
    
    log_func(f"______ _load_datadictionary_object(dataset_json={str(data_dictionary_json.get('id', ''))})")
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    
    data_dictionary_object = None
    if data_dictionary_json:
        # START if datasets_search_results
        return domo_objects.DataDictionary(
            id=data_dictionary_json.get('id', ''),
            # name=data_dictionary_json.get('name', ''),
            # data_dictionary_json=dataset_json.get('type'),
            # description=data_dictionary_json.get('description'),
            # row_count=data_dictionary_json.get('rowCount'),
            # column_count=data_dictionary_json.get('columnCount'),
            # owners=[] # Ownership data often requires separate API call, stubbing for now
        )
    # END if dataset_json

    log_func(f"______ END _load_datadictionary_object(dataset_json={str(data_dictionary_json.name)})")

    return data_dictionary_object
# END def _load_datadictionary_object

# =======================================================================
# PRIVATE: RETRIEVE A SINGLE PAGE OF DATASETS VIA PYDOMO
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param inst_url: The Domo instance URL prefix (for logging).
#     :param domo_ds_api: The PyDomo datasets client object.
#     :param limit: The number of records to retrieve (limit).
#     :param offset: The starting offset.
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _get_datasets_page (inst_url: str, domo_ds_api: Any, limit: int, offset: int, log_func: LogFunc) -> List[Dict[str, Any]]:
    log_func(f"______ _get_datasets_page(limit={limit}, offset={offset})")
    
    try:
        # PyDomo list() method returns dataset objects
        datasets_array = list(domo_ds_api.list(limit=limit, offset=offset))
    # END try
    except Exception as e:
        log_func(f"ERROR listing datasets via PyDomo SDK: {e}")
        return []
    # END except Exception as e

    log_func('______ END _get_datasets_page()')
    
    return datasets_array
# END def _get_datasets_page

# =======================================================================
# PRIVATE: FETCHES A PAGINATED LIST OF DATASETS (EXCLUDING DATASET VIEWS)
#     (PRIVATE) Fetches a paginated list of datasets, excluding "DataSet View" type via search API.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param count: The requested number of results (limit).
#     :param offset: The starting offset.
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionaries, or None on critical failure.
# =======================================================================
def _get_datasets_search_page (inst_url: str, inst_dev_token: str, limit: int, offset: int, log_func: LogFunc) -> Optional[List[dict]]:
    # log_func(f'________ _get_datasets_search_page ({inst_url} limit: {str(limit)}, offset: {str(offset)}')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
 
    api_url = f'https://{inst_url}.domo.com/api/data/ui/v3/datasources/search'
    
    body = {
        "entities": ["DATASET"],
        "filters": [{
            "filterType": "term",
            "field": "dataprovidername_facet",
            "value": "DataSet View", 
            "not": True 
        }],
        "combineResults": True, 
        "query": "*", 
        "count": count,
        "offset": offset,
        "sort": {
            "isRelevance": False, 
            "fieldSorts": [{"field": "create_date", "sortOrder": "DESC"}]
        }
    }

    resp = edao_http.post(api_url, inst_dev_token, log_func, body)
    
    dataset_objects = _load_dataset_objects (resp, log_func)
    
    # log_func(f'________ END _get_datasets_search_page ({inst_url} limit: {str(limit)}, offset: {str(offset)}')
    
    return dataset_objects
# END def _get_datasets_search_page

########################################################
# GET DATASETS BY YEARS
########################################################
def _get_datasets_by_years(inst_url: str, inst_dev_token: str, log_func: LogFunc):

    log_func(f"________ get_datasets_by_years( {str(inst_url)})")        
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_helper 

    # Get the current year and today's date
    today = edao_helper.get_current_time()
    current_year = today.year

    # Start date (January 1, 2000)
    # start_date = datetime.datetime(1999, 12, 31)
    start_year = _get_earliest_dataset_creation_year(inst_url, inst_dev_token, log_func)            
    # start_date = datetime.datetime(start_year, 1, 1)
    
    result = []

    # Loop through each year from start_year to the current year
    for year in range(start_year, current_year + 1):
        # Create start and end datetime objects for this year
        # start_of_year = datetime.datetime(year, 12, 31)
        start_of_year = datetime.datetime(year, 1, 1, 0, 0, 0)
        end_of_year = datetime.datetime(year, 12, 31, 23, 59, 59)
        # end_of_year = datetime.datetime(year+1, 1, 1)

        # If it's the current year, set the end date to now
        # if year+1 == current_year:
        if year == current_year:
            end_of_year = today
        # END if year == current_year:

        # Call the function to process the year's date range
        year_result = _get_datasets_by_date_range(inst_url, inst_dev_token, log_func, start_of_year, end_of_year)
        
        result.extend(year_result)
    # END for year in range(2000, current_year + 1):

    log_func('________ END get_datasets_by_years()')

    return result

# END addDatasetsToReportByYears():


########################################################
# GET DATASETS BY DATE RANGE
########################################################
def _get_datasets_by_date_range(inst_url: str, inst_dev_token: str, log_func: LogFunc, start_date, end_date):

    # log_func(f'______ _get_datasets_by_date_range({inst_url}, {str(start_date)}, {str(end_date)})')
    
    range_results = []
    page_size = 50
    offset = 0
    result_size = page_size # Initialize to ensure loop starts

    # The while loop remains the same for fetching pages
    while result_size == page_size:

        datasets_page_results = _get_datasets_by_date_range_page(inst_url, inst_dev_token, log_func, start_date, end_date, page_size, offset)

        if datasets_page_results is not None:

            page_results = datasets_page_results.get("dataSources", [])

            # 1. Update result_size to the count of items in the CURRENT page
            result_size = len(page_results) 
            log_func(f"_____________ Page size returned: {str(result_size)}")

            if result_size > 0:
                # Add all items from the current page to the final list
                range_results.extend(page_results)

                # 2. Increment offset by the size of the current page
                offset += result_size 

            # The loop condition `result_size == page_size` handles the break naturally
            # if the returned size is less than the requested page_size.
        
        # END if datasets_page_results is not None:
        else:
            log_func(f"_________ NO DATASETS FOUND or critical error at offset: {str(offset)}")
            break
        # END else (if datasets_page_results is not None:)
        
    # END while result_size == page_size:

    # log_func(f'______ END _get_datasets_by_date_range()')

    return range_results

# END addDatasetsToReportAPI():
                                    
############################
# GET DATASETS BY DATE RANGE PAGE
############################
def _get_datasets_by_date_range_page(inst_url, inst_dev_token, log_func: LogFunc, create_date_start, create_date_end, page_size, offset):

    # log_func(f'________ _get_datasets_by_date_range_page({inst_url}, {str(create_date_start)}, {str(create_date_end)}, {str(page_size)}, {str(offset)})')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http

    start_timestamp = int(create_date_start.timestamp() * 1000)
    end_timestamp = int(create_date_end.timestamp() * 1000)

    api_url = 'https://' + inst_url + '.domo.com' + '/api/data/ui/v3/datasources/search'

    body = {
                "entities": ["DATASET"],
                "filters":  [
                    {
                        "field": "create_date",
                        "filterType": "numeric",
                        "longNumber": start_timestamp,
                        "operator": "GT"
                    },
                    {
                        "field": "create_date",
                        "filterType": "numeric",
                        "longNumber": end_timestamp,
                        "operator": "LT"
                    }
                ],
                "combineResults": "true",
                # "combineResults": "false",
                "query": "*",
                "count": page_size,
                "offset": offset,
                "sort": {
                    "isRelevance": "false",
                    "fieldSorts": [{
                        "field": "create_date",
                        "sortOrder": "DESC"
                    }]
                }
            }

    # log_func('________ body' + str(body))
    datasets_page_results = edao_http.post(api_url, inst_dev_token, log_func, body)

    # log_func(f'________ END _get_datasets_by_date_range_page({inst_url}, {str(create_date_start)}, {str(create_date_end)}, {str(page_size)}, {str(offset)})')

    return datasets_page_results

# END _get_datasets_by_date_range_page():

############################
# GET EARLIEST CREATION YEAR
############################
def _get_earliest_dataset_creation_year(inst_url: str, inst_dev_token: str, log_func: LogFunc):

    # log_func(f'________ _get_earliest_dataset_creation_year({str(inst_url)})')
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http

    api_url = 'https://' + inst_url + '.domo.com' + '/api/data/ui/v3/datasources/search'

    body = {
                "entities": [
                    "DATASET"
                ],
                "filters": [],
                "combineResults": True,
                "query": "*",
                "count": 1,
                "offset": 0,
                "sort": {
                    "isRelevance": False,
                    "fieldSorts": [
                        {
                            "field": "create_date",
                            "sortOrder": "ASC"
                        }
                    ]
                }
            }

    resp = edao_http.post(api_url, inst_dev_token, log_func, body)

    result = None

    data_sources = resp["dataSources"]
    if len(data_sources) > 0:
        first_dataset = data_sources[0]
        created = first_dataset['created']
        created_date = datetime.datetime.fromtimestamp(created / 1000)
        
        result = created_date.year
    else:
        log_func(f'__________ _get_earliest_dataset_creation_year: the response is empty')
    # END if len(resp_json) > 0:

    # log_func(f'________ END get_earliest_dataset_creation_year({str(inst_url)})')

    return result

# END _get_earliest_dataset_creation_year(self, inst_name, inst_url, inst_dev_token):

