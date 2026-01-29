# randstadenterprise_edao_libraries/roles.py
import threading
from typing import List, Dict, Any, Optional, Callable

# Define the type for the log function
LogFunc = Callable[[str], None] 

# =======================================================================
# PRIVATE: FETCHES ALL ROLES AND ENRICHES THEM WITH GRANTS
#     (PRIVATE) Fetches all roles, then enriches each role object with its corresponding authorities (role grants).
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :returns: A list of domo_objects.Role objects.
# =======================================================================
def get_instance_roles (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Any]:

    log_func(f"____ get_instance_roles: {inst_url}")

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/authorization/v1/roles'
    
    resp = edao_http.get(api_url, inst_dev_token, log_func)

    # --- Enrich Roles with Grants ---
    # 2. Get the role grants map (mapped by authority name: 'EDIT_DASHBOARD')
    role_grants_map_by_authority = get_instance_role_grants(inst_url, inst_dev_token, log_func)
    
    # 3. Join roles with their grants and convert to Role objects
    inst_roles: List[objects.Role] = []
    
    for r in resp:
        r_id = str(r['id'])
        r_grants: Dict[str, domo_objects.RoleGrant] = {}
        
        # Build the grants map for this specific role
        for auth_name, grant_obj in role_grants_map_by_authority.items():
            if r_id in grant_obj.role_ids:
                r_grants[auth_name] = grant_obj
            # END if r_id in grant_obj.role_ids
        # END for auth_name, grant_obj in role_grants_map_by_authority.items()
                
        # Create the Role object
        role_obj = domo_objects.Role(
            id  =r_id,
            name = r.get('name', ''),
            description = r.get('description'),
            is_default = r.get('isDefault'),
            grants = r_grants
        )
        
        inst_roles.append(role_obj)
    # END for r_raw in inst_roles_raw

    log_func(f"____ END get_instance_roles: {inst_url}")
    
    return inst_roles
    
# END def _get_instance_roles

# =======================================================================
# RETRIEVES A SINGLE ROLE BY ID
#     Stubs out functionality to retrieve a single role by its ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param role_id: The string ID of the role.
#     :param log_func: Pre-bound logging function.
#     :returns: The domo_objects.Role object, or None if not found.
# =======================================================================
def get_role_by_id (inst_url: str, inst_dev_token: str, log_func: LogFunc, role_id: str) -> Optional[Any]:


    print(f"STUB: Getting role by ID {role_id} from {inst_url}")
    return None
# END def get_role_by_id

# =======================================================================
# RETRIEVES A SINGLE ROLE BY NAME
#     Stubs out functionality to retrieve a single role by its name.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param role_name: The name of the role.
#     :param log_func: Pre-bound logging function.
#     :returns: The domo_objects.Role object, or None if not found.
# =======================================================================
def get_role_by_name (inst_url: str, inst_dev_token: str, log_func: LogFunc, role_name: str) -> Optional[Any]:
    print(f"STUB: Getting role {role_name} from {inst_url}")
    return None
# END def get_role_by_name

# =======================================================================
# SAVES (CREATES OR UPDATES) A ROLE
#     Stubs out functionality to create or update a role.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param role_obj: The domo_objects.Role object (dataclass instance) to be saved.
#     :param log_func: Pre-bound logging function.
#     :returns: The string ID of the saved role, or None on failure.
# =======================================================================
def save_role (inst_url: str, inst_dev_token: str, log_func: LogFunc, role_obj: Any) -> Optional[str]:
    print(f"STUB: Saving role {role_obj.name} to {inst_url}")
    return role_obj.id
# END def save_role

# =======================================================================
# DELETES A ROLE BY ID
#     Stubs out functionality to delete a role.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param role_id: The string ID of the role to delete.
#     :param log_func: Pre-bound logging function.
#     :returns: True on success, False on failure.
# =======================================================================
def delete_role (inst_url: str, inst_dev_token: str, log_func: LogFunc, role_id: str) -> bool:
    print(f"STUB: Deleting role {role_id} from {inst_url}")
    return True
# END def delete_role


# =======================================================================
# FETCHES ALL AUTHORITIES AND MAPS THEM TO ROLE IDS
#     Fetches all authorities (role grants) in an instance and maps them to their respective Role IDs.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :returns: Dictionary mapping Role ID (str) to the domo_objects.RoleGrant object.
# =======================================================================
def get_instance_role_grants (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Any]:

    log_func(f'____ get_instance_role_grants({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/authorization/v1/authorities'
    
    role_grants_map: Dict[str, domo_objects.RoleGrant] = {}
    
    # 1. Fetch all authorities
    resp = edao_http.get(api_url, inst_dev_token, log_func)

    # 2. Iterate through authorities and map to all associated Role IDs
    for rg in resp:
        role_ids = [str(r_id) for r_id in rg.get('roleIds', [])]
        authority_name = rg['authority']

        # Create a RoleGrant object
        role_grant_obj = domo_objects.RoleGrant(
            authority=authority_name,
            role_ids=role_ids,
            description=rg.get('description')
        )

        # Map the RoleGrant object by its authority name (key)
        role_grants_map[authority_name] = role_grant_obj

    # END for rg in resp

    log_func(f'____ END get_instance_role_grants({inst_url})')
    
    return role_grants_map
    
# END def get_instance_role_grants

# =======================================================================
# PRIVATE: LOAD ROLE OBJECTS
#     (PRIVATE) Converts a json list to a List of Role objects
    
#     :param json: json array of data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of Role domo_objects.
# =======================================================================
def _load_role_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.Role instances.
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
            obj = _load_role_object(log_func, json_item)
            
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
# END def _load_role_objects()

# =======================================================================
# PRIVATE: LOAD ROLE OBJECT
#     (PRIVATE) Converts a json obj to a Role object
    
#     :param json: json of data
#     :param log_func: Pre-bound logging function.
#     :returns: A single Role object.
# =======================================================================
def _load_role_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.Role instance. 
    Raises an error if JSON is missing or if object creation fails.
    """
    
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_role_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the Role object
        return domo_objects.Role (
            id=json.get('id', ''),
            name=json.get('name', ''),
            description=json.get('description', ''),
            is_default=json.get('isDefault', '')
        )       
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.Role. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_role_object() -> Any:    


# =======================================================================
# PRIVATE: LOAD ROLE GRANT OBJECTS
#     (PRIVATE) Converts a json list to a List of RoleGrant objects
    
#     :param json: json array of data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of RoleGrant objects.
# =======================================================================
def _load_role_grant_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.RoleGrant instances.
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
            obj = _load_role_grant_object(log_func, json_item)
            
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
# END def _load_role_grant_objects()

# =======================================================================
# PRIVATE: LOAD ROLE OBJECT
#     (PRIVATE) Converts a json obj to a Role object
    
#     :param json: json of role data
#     :param log_func: Pre-bound logging function.
#     :returns: A single Role object.
# =======================================================================
def _load_role_grant_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.RoleGrant instance. 
    Raises an error if JSON is missing or if object creation fails.
    """
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_role_grant_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the RoleGrant object
        return domo_objects.RoleGrant (
            authority=json.get('authority', ''),
            # title=json.get('title', ''),
            description=json.get('description', ''),
            role_ids = []
        )       
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.RoleGrant. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_role_grant_object() -> Any:    

