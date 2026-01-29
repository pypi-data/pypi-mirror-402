# randstadenterprise_edao_libraries/assets.py
from typing import List, Dict, Any, Optional, Callable, Union

# Define the type for the log function for clean type hinting
LogFunc = Callable[[str], None] 

# =======================================================================
# CORE API RETRIEVAL FUNCTIONS (GET_ALL)
# =======================================================================

# =======================================================================
#     Retrieves ALL repositories (owned or shared) from a Domo instance by handling full pagination.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :returns: A single list containing all raw asset dictionary objects.
# =======================================================================
def get_instance_assets (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Any]:

    log_func(f'____ get_instance_assets({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects     
    
    all_assets: List[domo_objects.Asset] = [] 
    
    asset_page_results = _get_instance_assets_page (inst_url, inst_dev_token, log_func, 0, 30)
    all_assets = _load_asset_objects(log_func, asset_page_results)

    log_func(f"_______ TOTAL ASSETS: {str(len(all_assets))}")
    
    log_func(f"____ END get_instance_assets: {inst_url}")
    
    return all_assets

# END def get_instance_assets

# =======================================================================
#     Retrieves a repository by id
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param asset_id: The exact id of the asset to find.
#     :returns: A single asset object.
# =======================================================================
def get_asset_by_id (inst_url: str, inst_dev_token: str, log_func: LogFunc, asset_id: str) -> Any:

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    log_func(f'____ get_asset_by_id({inst_url})')
    api_url = f"https://{inst_url}.domo.com/api/apps/v1/designs/{asset_id}?parts=owners%2Ccards%2Cversions%2Ccreator"

    resp = edao_http.get(api_url, inst_dev_token, log_func)
    
    asset_object = _load_asset_object(log_func, resp)
        
    log_func(f"____ END get_asset_by_id: {inst_url}")
    
    return asset_object

# END def get_asset_by_id

# =======================================================================
    # Updates the ADMIN permissions (owners) for a specific Domo App Asset.
    # Safeguard: Ensures the current owner is included in the new owners list to prevent lockout.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param asset_id: The exact id of the asset to find.
#     :param owners: A list of user id strings to add as owners
#     :returns: The string ID of the promoted repository, or None on failure.
# =======================================================================
def set_asset_owners(inst_url: str, inst_dev_token: str, log_func: LogFunc, asset_id: str, owners: List[str]) -> Optional[str]:

    log_func(f'____ set_asset_owners({inst_url}, Asset ID: {asset_id})')  
    
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http     
    
    # 1. Fetch current asset to verify the current owner
    asset = get_asset_by_id(inst_url, inst_dev_token, log_func, asset_id)
    
    # Validation: Ensure the current owner is not being removed
    # Assuming asset.owner returns the owner's User ID string
    asset_owner_id = str(asset.owner)
    
    ext_asset_owners = asset.owners
    ext_owner_ids = []
    # 2. Remove all additional owners
    for ext_owner in ext_asset_owners:
        remove_owner_id = str(ext_owner["id"])
        if str(asset_owner_id) != remove_owner_id:
            ext_owner_ids.append(remove_owner_id)
        # END if asset_owner_id != remove_owner_id:
    # END for ext_owner in ext_asset_owners:
    remove_asset_owners (inst_url, inst_dev_token, log_func, asset_id, ext_owner_ids)
    
    # 3. Set all the provided owners
    # The API expects a list of User IDs as the body
    owners.append(asset_owner_id)    
    body = owners
    api_url = f"https://{inst_url}.domo.com/api/apps/v1/designs/{asset_id}/permissions/ADMIN"
    resp = edao_http.post(api_url, inst_dev_token, log_func, body)
        
    log_func(f"____ END set_asset_owners: {inst_url}")
    
    return "SUCCESS"

# END def set_asset_owners

# =======================================================================
#     Add Asset Owners
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param asset_id: The exact id of the asset to find.
#     :param owner_ids: List of user id to add as owners
#     :returns: The string ID of the promoted repository, or None on failure.
# =======================================================================
def add_asset_owners (inst_url: str, inst_dev_token: str, log_func: LogFunc, asset_id: str, owner_ids:List[str]) -> Optional[str]:

    log_func(f'____ add_asset_owner({inst_url})')  

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    body = owner_ids
    api_url = f"https://{inst_url}.domo.com/api/apps/v1/designs/{asset_id}/permissions/ADMIN"
    
    resp = edao_http.post(api_url, inst_dev_token, log_func, body)
        
    log_func(f"____ END add_asset_owner: {inst_url}")
    
    return "SUCCESS"

# END def add_asset_owner

# =======================================================================
#     Remove Asset Owner
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param asset_id: The exact id of the asset to find.
#     :param owner_ids: List of user id to remove as owners
#     :returns: The string ID of the promoted repository, or None on failure.
# =======================================================================
def remove_asset_owners (inst_url: str, inst_dev_token: str, log_func: LogFunc, asset_id: str, owner_ids:List[str]) -> Optional[str]:

    log_func(f'____ remove_asset_owner({inst_url})') 
    
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    asset = get_asset_by_id(inst_url, inst_dev_token, log_func, asset_id)
    asset_owner_id = str(asset.owner)

    for owner_id in owner_ids:
        if asset_owner_id != owner_id:
            api_url = f"https://{inst_url}.domo.com/domoapps/designs/{asset_id}/permissions/ADMIN/ids?users={owner_id}"
            resp = edao_http.delete(api_url, inst_dev_token, log_func)
        # END if asset_owner_id != remove_owner_id:
    # END for ext_owner in ext_asset_owners:
            
    log_func(f"____ END remove_asset_owner: {inst_url}")
    
    return "SUCCESS"  

# END def remove_asset_owner

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# =======================================================================
# PRIVATE: LOAD ASSET OBJECTS
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param datasets_json: json array of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_asset_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.Asset instances.
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
            obj = _load_asset_object(log_func, json_item)
            
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
# END def _load_asset_objects

# =======================================================================
# PRIVATE: LOAD ASSET OBJECT
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param json: json of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_asset_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.Asset instance. 
    Raises an error if JSON is missing or if object creation fails.
    """

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    
    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_asset_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the Asset object
        return domo_objects.Asset (
            asset_id=json.get('id', ''),
            name=json.get('name', ''),
            owner=json.get('owner', ''),

            created_by=json.get('createdBy', ''),
            created_date=json.get('createdDate', ''),
            updated_by=json.get('updatedBy', ''),
            updated_date=json.get('updatedDate', ''),

            latest_version=json.get('latestVersion', ''),
            owners=json.get('owners', {}),
            creator=json.get('creator', {}),
            
            # Now fields with defaults
            description=json.get('description', None),
            versions=json.get('versions', {}),
            instances=json.get('instances', []),
            referencing_cards=json.get('referencingCards', []),

            deleted_date=json.get('deletedDate', None),
            trusted=json.get('trusted', False),
            has_thumbnail=json.get('hasThumbnail', True),

        )       
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.Asset. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_asset_object(log_func: LogFunc, json: Any) -> Any:    


# =======================================================================
# =======================================================================
# =======================================================================
# PRIVATE API HELPER FUNCTIONS
# =======================================================================
# =======================================================================
# =======================================================================

# =======================================================================
# (PRIVATE HELPER) Fetches a single paginated result of assests.
#     Used by get_instance_assests
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param offset: The starting index for pagination.
#     :param limit: The number of results to return.
#     :returns: The raw JSON response dictionary containing 'assets' or an empty dict on error.
# =======================================================================
def _get_instance_assets_page (inst_url: str, inst_dev_token: str, log_func: LogFunc, offset: int, limit: int) -> Any:

    log_func(f'_______ _get_instance_assets_page(offset: {str(offset)}, limit: {str(limit)})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url_query = f'?checkAdminAuthority=true&deleted=false&direction=desc&limit={limit}&offset={offset}&order=updated&parts=owners&parts=creator&parts=thumbnail&parts=versions&search=&withPermission=ADMIN'
    api_url = f'https://{inst_url}.domo.com/api/apps/v1/designs{api_url_query}'
    
    page_result = edao_http.get(api_url, inst_dev_token, log_func)
        
    log_func('_______ END _get_instance_assets_page()')

    return page_result
# END def _get_instance_assets_page