# randstadenterprise_edao_libraries/domo_groups.py
import base64  
from typing import List, Dict, Any, Optional, Callable

# Define the type for the log function for clean type hinting
LogFunc = Callable[[str], None] 

# =======================================================================
# GROUP API RETRIEVAL FUNCTIONS
# =======================================================================

# =======================================================================
# FETCHES ALL GROUPS AND MAPS BY LOWERCASE NAME
#     Fetches all groups in an instance and returns them mapped by lowercase group name.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function for this instance.
#     :returns: A dictionary mapping lowercase group names to the objects.Group object, or None on critical failure.
# =======================================================================
def get_instance_groups (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Any]:
    
    log_func(f'__________ Calling get_all_instance_groups for {inst_url}')
    
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/content/v2/groups'
    
    inst_groups: List[objects.Group] = []
    
    # 1. Fetch groups list
    groups_json = edao_http.get(api_url, inst_dev_token, log_func)

    if isinstance(groups_json, list):
        
        inst_groups =  _load_group_objects(log_func, groups_json)
       
    # END if isinstance(groups_json, list):

    return inst_groups
        
# END def get_instance_groups

# =======================================================================
# RETRIEVES A SINGLE GROUP BY ID
#     retrieve a single group by its name.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param group_id: The id of the group.
#     :returns: The domo_objects.Group object, or None if not found.
# =======================================================================
def get_group_by_id (inst_url: str, inst_dev_token: str, log_func: LogFunc, group_id: str) -> Optional[Any]:
    
    log_func(f"Getting group id {group_id} from {inst_url}")
    
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/content/v2/groups/{group_id}?includeUsers=true'

    # 1. Fetch group
    group_json = edao_http.get(api_url, inst_dev_token, log_func)
    
    group_obj = _load_group_object(log_func, group_json)
                 
    return group_obj
# END def get_group_by_id

# =======================================================================
# RETRIEVES A SINGLE GROUP BY NAME
#     retrieve a single group by its name.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param group_name: The name of the group.
#     :returns: The domo_objects.Group object, or None if not found.
# =======================================================================
def get_group_by_name(inst_url: str, inst_dev_token: str, log_func: LogFunc, group_name: str) -> Optional[Any]:
    
    log_func(f"Getting group name {group_name} from {inst_url}")
    
    # 1. Get the map (keys are already lowercased in the helper function)
    groups_map = _get_instance_groups_map(inst_url, inst_dev_token, log_func)

    # 2. Lookup using lowercase key
    # Since the map already contains domo_objects.Group instances, we just return the value directly
    if group_name.lower() in groups_map:
        g = groups_map[group_name.lower()]
        
        group_id = g.id
        return get_group_by_id (inst_url, inst_dev_token, log_func, group_id)
        
    # END if group_name.lower() in groups_map:
    
    return None
# END def get_group_by_name

# =======================================================================
# GROUP MODIFICATION FUNCTIONS (All Public)
# =======================================================================

# =======================================================================
# PUBLIC: CREATES A NEW GROUP VIA API
#     Creates a new group in the destination instance.
    
#     :param inst_url: URL prefix of the destination instance.
#     :param dest_inst_devtok: Developer token for the destination instance.
#     :param log_func: Pre-bound logging function.
#     :param src_group: The source group dictionary providing name, description, and type.
#     :returns: The domo_objects.Group object if successful, None otherwise.
# =======================================================================
# def create_group (inst_url: str, inst_dev_token: str, log_func: LogFunc, src_group: domo_objects.Group) -> Optional[objects.Group]:
    
#     logging.info(f"API Call: Creating group '{src_group['name']}' in {inst_url}")
    
#     body = {
#         "name": src_group.name,
#         "description": src_group.description,
#         "type": src_group.get("groupType", "open") # Default to 'open' if not specified
#     }
#     api_url = f"https://{dest_inst_url}.domo.com/api/content/v2/groups"
    
#     new_group = edao_http.post(api_url, inst_dev_token, body)

#     logging.info(f"Successfully created group '{src_group['name']}'.")

#     return domo_objects.Group(
#         id=str(new_group.get('id', '')),
#         name=new_group.get('name', 'N/A'), # Mandatory field
#         type=new_group.get('groupType', 'GROUP'), # Mandatory field: Must be passed
#         group_type=new_group.get('groupType'),
#         description=new_group.get('description'),
#     )
# # END def create_group

# =======================================================================
# SAVES (CREATES OR UPDATES) A GROUP
#     Stubs out functionality to create or update a group.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param group_obj: The domo_objects.Group object (dataclass instance) to be saved.
#     :param log_func: Pre-bound logging function.
#     :returns: The string ID of the saved group, or None on failure.
# =======================================================================
# def save_group (inst_url: str, inst_dev_token: str, log_func: LogFunc, group_obj: domo_objects.Group) -> Optional[str]:
#     print(f"STUB: Saving group {group_obj.name} to {inst_url}")
#     return group_obj.id
# # END def save_group

# =======================================================================
# DELETES A GROUP BY ID
#     Stubs out functionality to delete a group.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param group_id: The string ID of the group to delete.
#     :param log_func: Pre-bound logging function.
#     :returns: True on success, False on failure.
# =======================================================================
# def delete_group (inst_url: str, inst_dev_token: str, log_func: LogFunc, group_id: str) -> bool:
#     print(f"STUB: Deleting group {group_id} from {inst_url}")
#     return True
# # END def delete_group


# =======================================================================
# PUBLIC: UPDATES GROUP NAME, DESC, AND DYNAMIC DEFINITION
#     Updates a group's attributes (name, description, dynamic definition) in the destination instance.
    
#     :param src_group: Source group details for attributes.
#     :param dest_inst_url: URL prefix of the destination instance.
#     :param dest_inst_devtok: Developer token for the destination instance.
#     :param dest_group: Current destination group details (needed for 'groupId').
#     :param log_func: Pre-bound logging function.
#     :returns: None
# =======================================================================
# def save_group_attributes (inst_url: str, inst_dev_token: str, log_func: LogFunc, (src_group: Dict[str, Any], dest_group: Dict[str, Any]) -> None:
    
#     logging.info(f"API Call: Saving attributes for group '{dest_group['name']}' in {inst_url}")
    
#     # 1. Build the base body for the PUT request
#     body = [{
#         "groupId": dest_group["groupId"],
#         "name": src_group["name"],
#         "description": src_group.get("description", ""),
#         "type": src_group.get("groupType", "open"),
#     }]
    
#     # 2. Add dynamic definition only if it exists in the source
#     if "permissions" in src_group and src_group.get("groupType") == "dynamic":
#         permissions = src_group["permissions"].copy()
#         # Remove owner data as it's handled separately
#         permissions.pop("owners", None)
#         permissions.pop("isCurrentUserOwner", None)
#         body[0]["dynamicDefinition"] = permissions
#         # END if "permissions" in src_group and src_group.get("groupType") == "dynamic"

#     api_url = f"https://{dest_inst_url}.domo.com/api/content/v2/groups"
#     resp = requests.put(api_url, headers=helpers.get_http_headers(dest_inst_devtok), json=body)

#     if resp.status_code not in [200, 201]:
#         logging.error(f"Failed to save group attributes. Status: {resp.status_code}, Reason: {resp.text}")
#         # END if resp.status_code not in [200, 201]
# # END def save_group_attributes
        

# =======================================================================
# PUBLIC: ADDS/REMOVES OWNERS TO MATCH DEFINED LIST
#     Ensures the destination group's owners match the hardcoded list 
#     by performing ADD and REMOVE operations.
    
#     :param dest_inst_url: URL prefix of the destination instance.
#     :param dest_inst_devtok: Developer token.
#     :param dest_group: Current destination group details.
#     :param dest_group_owners_list: The list of desired owner names (strings).
#     :param get_group_map_func: Function to retrieve group map (for owner ID lookup).
#     :param get_group_details_func: Function to retrieve full group details (for owner refresh).
#     :param dest_inst_name: Name of the destination instance.
#     :param log_func: Pre-bound logging function.
#     :returns: None
# =======================================================================
# def save_group_owners (inst_url: str, inst_dev_token: str, log_func: LogFunc, dest_group: Dict[str, Any], dest_group_owners_list: List[str], dest_inst_name: str) -> None:

#     logging.info(f"Configuring owners for group '{dest_group['name']}' to match the defined list.")

#     # 1. Get the group map again to find IDs of desired owners
#     dest_group_map = get_group_map_func(dest_inst_name, dest_inst_url, dest_inst_devtok)
#     current_owners = {owner["displayName"]: owner for owner in dest_group.get("owners", [])}
#     logging.debug(f"Current owners are: {list(current_owners.keys())}")

#     # Step 1: Determine which owners to ADD.
#     add_owners = []
#     for owner_name in dest_group_owners_list:
#         if owner_name not in current_owners:
#             owner_to_add = dest_group_map.get(owner_name)
#             if owner_to_add:
#                 # Assuming the GroupMapGetterFunc returns dicts with 'groupId' or domo_objects.Group objects
#                 owner_id = owner_to_add.id if isinstance(owner_to_add, domo_objects.Group) else owner_to_add.get('groupId')
                
#                 # Use the ID from the dest_group_map (assuming it contains groupId)
#                 add_owners.append({"type": "GROUP", "id": owner_id})
#             else:
#                 logging.warning(f"Desired owner group '{owner_name}' does not exist in '{dest_inst_name}' and cannot be added.")
#                 # END else
#             # END if owner_to_add
#         # END if owner_name not in current_owners
#     # END for owner_name in dest_group_owners_list

#     # 2a. Execute ADD API call
#     if add_owners:
#         logging.info(f"Step 1: Adding {len(add_owners)} new owner(s).")
#         api_url = f"https://{dest_inst_url}.domo.com/api/content/v2/groups/access"
#         add_body = [{"groupId": dest_group["groupId"], "addOwners": add_owners, "removeOwners": []}]
#         add_resp = requests.put(api_url, headers=helpers.get_http_headers(dest_inst_devtok), json=add_body)
#         if add_resp.status_code not in [200, 201]:
#             logging.error(f"Failed to add owners. Status: {add_resp.status_code}, Reason: {add_resp.text}")
#             return # Stop if adding fails.
#             # END if add_resp.status_code not in [200, 201]
#     else:
#         # START else
#         logging.info("Step 1: No new owners to add.")
#         # END else
#     # END if add_owners

#     # Step 2: Determine which owners to REMOVE.
#     # 2b. Refresh the group details to get the most current owner list
#     # The return type of get_group_details_func is assumed to be domo_objects.Group
#     refreshed_group = get_group_details_func(dest_inst_name, dest_inst_url, dest_inst_devtok, dest_group["name"])
#     if not refreshed_group: return # Safety check
    
#     # NOTE: The dest_group dictionary passed to this function must contain the 'owners' field from a previous API call, 
#     # not just the dataclass. For now, we rely on the helper functions to retrieve the raw dict.
    
#     # We assume 'owners' key in the raw dict structure for simplicity here
#     refreshed_owners = {owner["displayName"]: owner for owner in refreshed_group.get("owners", [])}

#     # Identify owners currently on the group that are NOT in the desired list
#     remove_owners = [
#         {"type": owner["type"], "id": owner["id"]}
#         for name, owner in refreshed_owners.items()
#         if name not in dest_group_owners_list
#     ]

#     # 3a. Execute REMOVE API call
#     if remove_owners:
#         logging.info(f"Step 2: Removing {len(remove_owners)} outdated owner(s).")
#         api_url = f"https://{dest_inst_url}.domo.com/api/content/v2/groups/access"
#         remove_body = [{"groupId": dest_group["groupId"], "addOwners": [], "removeOwners": remove_owners}]
#         remove_resp = requests.put(api_url, headers=helpers.get_http_headers(dest_inst_devtok), json=remove_body)
#         if remove_resp.status_code not in [200, 201]:
#             logging.error(f"Failed to remove outdated owners. Status: {remove_resp.status_code}, Reason: {remove_resp.text}")
#             # END if remove_resp.status_code not in [200, 201]
#     else:
#         logging.info("Step 2: No outdated owners to remove.")
#         # END else
#     # END if remove_owners
# # END def save_group_owners

# =======================================================================
# PUBLIC: COPIES GROUP AVATAR IMAGE
#     Copies the group's avatar/image from the source to the destination 
#     instance using base64 encoding.
    
#     :param src_inst_url: URL prefix of the source instance.
#     :param src_inst_devtok: Developer token for the source instance.
#     :param src_group: Source group details (needed for 'groupId').
#     :param dest_inst_url: URL prefix of the destination instance.
#     :param dest_inst_devtok: Developer token for the destination instance.
#     :param dest_group: Destination group details (needed for 'groupId').
#     :param log_func: Pre-bound logging function.
#     :returns: None
# =======================================================================
# def save_group_image (inst_url: str, inst_dev_token: str, log_func: LogFunc, src_group: Dict[str, Any], dest_inst_url: str, dest_inst_devtok: str, dest_group: Dict[str, Any]) -> None:
#     logging.info(f"API Call: Saving image for group '{dest_group['name']}' in {dest_inst_url}")
    
#     # 1. Retrieve the image from the source instance
#     src_img_url = f"https://{src_inst_url}.domo.com/api/content/v1/avatar/GROUP/{src_group['groupId']}"
#     src_img_resp = requests.get(src_img_url, headers=helpers.get_http_headers(src_inst_devtok))

#     if src_img_resp.status_code != 200:
#         logging.warning(f"Could not retrieve source group image. Status: {src_img_resp.status_code}")
#         return
#         # END if src_img_resp.status_code != 200

#     # 2. Encode image to base64 data URL
#     base64_str = base64.b64encode(src_img_resp.content).decode('utf-8')
#     data_url = f"data:image/png;base64,{base64_str}"
    
#     # 3. Upload the image to the destination instance
#     dest_url = f"https://{dest_inst_url}.domo.com/api/content/v1/avatar/GROUP/{dest_group['groupId']}"
#     body = {"encodedImage": data_url}

#     dest_img_resp = requests.post(dest_url, json=body, headers=helpers.get_http_headers(dest_inst_devtok))
#     if dest_img_resp.status_code not in [200, 201, 204]:
#         logging.error(f"Failed to save group image. Status: {dest_img_resp.status_code}, Reason: {dest_img_resp.text}")
#     # END if dest_img_resp.status_code not in [200, 201, 204]
# # END def save_group_image


# =======================================================================
# =======================================================================
# =======================================================================
# PRIVATE API HELPER FUNCTIONS
# =======================================================================
# =======================================================================
# =======================================================================
def _get_instance_groups_map(inst_url: str, inst_dev_token: str, log_func: LogFunc) -> Dict[str, Any]:
    
    log_func(f'__________ Calling _get_instance_groups_map for {inst_url}')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 
    
    api_url = f'https://{inst_url}.domo.com/api/content/v2/groups'
    
    inst_groups_map: Dict[str, domo_objects.Group] = {}
    
    # 1. Fetch groups list
    groups_json = edao_http.get(api_url, inst_dev_token, log_func)

    if isinstance(groups_json, list):
        # 2. Map groups by lowercase name
        for g in groups_json:
            if isinstance(g, dict) and "name" in g:

                group_name = g.get('name')
                
                # Fully populate the object here so the cache is complete
                group_obj = domo_objects.Group(
                    id=str(g.get('id', '')),
                    name=group_name, # Mandatory field
                    type=g.get('groupType', 'GROUP'), # Mandatory field
                    
                    group_type=g.get('groupType'),
                    description=g.get('description'),
                    owners=g.get('owners'),
                    user_ids=g.get('userIds'),
                    users=g.get('users'),
                    active=g.get('active'),
                    created=g.get('created'),
                    creator_id=g.get('creatorId'),
                    default=g.get('default'),
                    guid=g.get('guid'),
                    hidden=g.get('hidden'),
                    member_count=g.get('memberCount'),
                    modified=g.get('modified')
                )                    

                # Key logic: Use .lower() for case-insensitive lookup
                inst_groups_map[group_name.lower()] = group_obj
            # END if isinstance
        # END for g
    # END if isinstance

    return inst_groups_map
        
# END def _get_instance_groups_map


# =======================================================================
# PRIVATE: LOAD GROUP OBJECTS
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param datasets_json: json array of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_group_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.Group instances.
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
            obj = _load_group_object(log_func, json_item)
            
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
# END def _load_group_objects

# =======================================================================
# PRIVATE: LOAD GROUP OBJECT
#     (PRIVATE) Retrieves a single page of datasets using the PyDomo SDK.
    
#     :param json: json of dataset data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_group_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.Group instance. 
    Raises an error if JSON is missing or if object creation fails.
    """
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_group_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
                
        # Fully populate the object here so the cache is complete
        return domo_objects.Group(
            id=str(json.get('id', '')),
            name=json.get('name'), # Mandatory field
            type=json.get('groupType', 'GROUP'), # Mandatory field

            group_type=json.get('groupType'),
            description=json.get('description'),
            owners=json.get('owners'),
            user_ids=json.get('userIds'),
            users=json.get('users'),
            active=json.get('active'),
            created=json.get('created'),
            creator_id=json.get('creatorId'),
            default=json.get('default'),
            guid=json.get('guid'),
            hidden=json.get('hidden'),
            member_count=json.get('memberCount'),
            modified=json.get('modified')
        )          
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.Group. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_group_object(log_func: LogFunc, json: Any) -> Any:    
