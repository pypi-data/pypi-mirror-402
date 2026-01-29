# randstadenterprise_edao_libraries/domo_users.py
from typing import List, Dict, Any, Optional, Callable

# Define the type for the log function
LogFunc = Callable[[str], None] 

# Type for a map of attributes (key -> attribute details)
AttrMap = Dict[str, Dict[str, Any]]

USER_SYNC_ATTRS = {
        "id":{"sync":False,"key":"id","name":"ID","desc":"Person's id","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "roleId":{"sync":False,"key":"roleId","name":"Role ID","desc":"Person's roleId","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"},
        "created":{"sync":False,"key":"created","name":"Created Date","desc":"Person's created date","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "lastActivity":{"sync":False,"key":"lastActivity","name":"Last Activity","desc":"Person's lastActivity date","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "displayName":{"sync":False,"key":"displayName","name":"Display Name","desc":"Person's display name","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "groups":{"sync":False,"key":"groups","name":"Groups","desc":"Person's groups","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "emailAddress":{"sync":False,"key":"emailAddress","name":"Email Address","desc":"Person's email address","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "reportsTo":{"sync":True,"key":"reportsTo","name":"Reports To ID","desc":"Person's reports to id","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "modified":{"sync":False,"key":"modified","name":"Modified Date","desc":"Person's modified date","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"},      
        "employeeNumber":{"sync":False,"key":"employeeNumber","name":"Employee number","desc":"Person's employee number (number only)","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "employeeId":{"sync":False,"key":"employeeId","name":"Employee ID","desc":"Person's employee id (alphanumeric)","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "department":{"sync":True,"key":"department","name":"Department","desc":"Person's department","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "title":{"sync":True,"key":"title","name":"Title","desc":"Person's title","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "locale":{"sync":False,"key":"locale","name":"Local","desc":"Person's locale","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "timeZone":{"sync":False,"key":"timeZone","name":"Time zone","desc":"Person's timezone","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "employeeLocation":{"sync":True,"key":"employeeLocation","name":"Location","desc":"Person's location","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        "phoneNumber":{"sync":True,"key":"phoneNumber","name":"Phone Number","desc":"Person's phoneNumber","validator":"ANY_VALUE","valueType":"null","keyspace":"domo-defined"}, 
        
        "syncattrs":{"sync":False,"key":"syncattrs","name":"Sync Attrs","desc":"Used for user sync automation","validator":"ANY_VALUE","valueType":"STRING","keyspace":"customer-defined"}, 
        "syncrole":{"sync":False,"key":"syncrole","name":"Sync role","desc":"Used for user sync automation","validator":"ANY_VALUE","valueType":"STRING","keyspace":"customer-defined"},
        "accountname":{"sync":True,"key":"accountname","name":"Account","desc":"Name of the Client Account","validator":"ANY_VALUE_MULTI","valueType":"STRING","keyspace":"customer-defined"}, 
        "programname":{"sync":True,"key":"programname","name":"Program","desc":"A program is a subset of a client account, specifying a staffing program we deliver for client account","validator":"ANY_VALUE_MULTI","valueType":"STRING","keyspace":"customer-defined"}, 
        "membership":{"sync":True,"key":"membership","name":"Member of","desc":"The user belongs to defined Leadership teams, management bodies or Steer-Co's","validator":"ANY_VALUE_MULTI","valueType":"STRING","keyspace":"customer-defined"}, 
        "useractivity":{"sync":False,"key":"useractivity","name":"Users and Activity","desc":"Identifies if the user has access to the Users and Activity pages","validator":"ANY_VALUE_MULTI","valueType":"STRING","keyspace":"customer-defined"}, 
        "project":{"sync":True,"key":"project","name":"Project","desc":"Identifies if the user has access to various Projects","validator":"ANY_VALUE_MULTI","valueType":"STRING","keyspace":"customer-defined"}, 
        "entity":{"sync":True,"key":"entity","name":"Entity","desc":"client company or randstad entity the user belongs to","validator":"ANY_VALUE_MULTI","valueType":"STRING","keyspace":"customer-defined"}
         
    }

# =======================================================================
# RETRIEVES ALL USERS, ENRICHES DATA, AND MAPS BY USER ID
#     Retrieves all instance users, enriches the data with readable fields, 
#     and returns a map of the full domo_objects.User object by User ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.

#     :returns: Dictionary mapping User ID (str) to the domo_objects.User object.
# =======================================================================

def get_instance_users (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Any]:
    
    log_func(f"____ get_instance_users: {inst_url}")
    
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects
    from . import domo_roles

    # 1. Get Role Map for lookup using the roles function
    roles_map = domo_roles.get_instance_roles(inst_url, inst_dev_token, log_func)
    
    # 2. Get raw user data using the private search helper
    inst_users = _get_instance_users_search(inst_url, inst_dev_token, log_func, USER_SYNC_ATTRS)
    
    users: List[objects.User] = []

    # 3. Process and enrich each user record
    for u in inst_users:        
        # Process Custom attributes into Dict[str, List[str]] format
        u_attrs_map: Dict[str, List[str]] = {}
        if "attributes" in u:
            u_attrs = u['attributes']            
            for a in u_attrs:
                key = a.get("key")
                values = a.get("values", [])
                if key: u_attrs_map[key] = values
            # END for a in u_attrs
        # END if "attributes" in u_raw
        
        # Process Groups
        groups_list: List[str] = []
        if "groups" in u:
            for g in u['groups']:
                if g.get("name"): groups_list.append(g["name"])
            # END for g in u_raw['groups']
        # END if "groups" in u_raw
        
        # 4. Create the User object
        user_obj = domo_objects.User(
            id=str(u.get('id', '')),
            email_address=u.get('emailAddress', ''),
            name=u.get('displayName'), # Owner base class name maps to displayName
            type='USER',
            user_name=u.get('userName'),
            role_id=str(u.get('roleId')),
            last_activity=u.get('lastActivity'),
            groups=groups_list,
            attributes=u_attrs_map
        )
        
        # 5. Add to the return map
        users.append(user_obj)
        
    # END for u in inst_users
    
    log_func(f"____ END get_instance_users: {inst_url}")
 
    return users
# END def get_instance_users

# =======================================================================
# RETRIEVES A SINGLE USER BY EMAIL ADDRESS
#     Stubs out functionality to retrieve a single user by their email address.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param user_email: The email address of the user.
#     :param log_func: Pre-bound logging function.
#     :returns: The domo_objects.User object, or None if not found.
# =======================================================================
# def get_user_by_email (inst_url: str, inst_dev_token: str, log_func: LogFunc, user_email: str) -> Optional[objects.User]:
#     print(f"STUB: Getting user {user_email} from {inst_url}")
#     return None
# # END def get_user_by_email

# =======================================================================
# RETRIEVES A SINGLE USER BY ID
#     Stubs out functionality to retrieve a single user by their ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param user_id: The string ID of the user.
#     :param log_func: Pre-bound logging function.
#     :returns: The domo_objects.User object, or None if not found.
# =======================================================================
# def get_user_by_id (inst_url: str, inst_dev_token: str, log_func: LogFunc, user_id: str) -> Optional[objects.User]:
#     print(f"STUB: Getting user by ID {user_id} from {inst_url}")
#     return None
# # END def get_user_by_id

# =======================================================================
# RETRIEVES A SINGLE USER BY ID
#     Stubs out functionality to retrieve a single user by their ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param user_id: The string ID of the user.
#     :param log_func: Pre-bound logging function.
#     :returns: The domo_objects.User object, or None if not found.
# =======================================================================
# def get_user_by_id (inst_url: str, inst_dev_token: str, log_func: LogFunc, user_id: str) -> Optional[objects.User]:
#     print(f"STUB: Getting user by ID {user_id} from {inst_url}")
#     return None
# # END def get_user_by_id

# =======================================================================
# USER ATTRIBUTES RETRIEVAL
# =======================================================================

# =======================================================================
# FETCHES ALL USER ATTRIBUTES AND MAPS THEM BY KEY
#     Fetches all instance user attributes and returns them mapped by attribute key.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :returns: Dictionary mapping attribute key (str) to attribute details.
# =======================================================================
def get_all_instance_user_attributes (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> AttrMap:
    
    log_func(f'____________________ get_all_instance_user_attributes({inst_url})')
    
    inst_attrs_map = {}
    
    # 1. Call the private API function to get raw attributes
    inst_attrs = _get_instance_attributes(inst_url, inst_dev_token, log_func)
    
    # 2. Map attributes by their full key
    for a in inst_attrs:
        # START for a in inst_attrs
        full_key = a['key']
        inst_attrs_map[full_key] = a
        # END for a in inst_attrs
    
    log_func('____________________ END get_all_instance_user_attributes()')

    return inst_attrs_map
# END def get_all_instance_user_attributes

# =======================================================================
# RETRIEVES A SINGLE USER ATTRIBUTE BY NAME
#     Stubs out functionality to retrieve a single user attribute by its display name.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param attribute_name: The display name of the attribute.
#     :param log_func: Pre-bound logging function.
#     :returns: The attribute dictionary, or None if not found.
# =======================================================================
# def get_user_attribute_by_name (inst_url: str, inst_dev_token: str, attribute_name: str, log_func: LogFunc) -> Optional[Dict[str, Any]]:
#     print(f"STUB: Getting user attribute {attribute_name} from {inst_url}")
#     return None
# # END def get_user_attribute_by_name

# =======================================================================
# RETRIEVES A SINGLE USER ATTRIBUTE BY ID
#     Stubs out functionality to retrieve a single user attribute by its ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param attribute_id: The string ID of the attribute.
#     :param log_func: Pre-bound logging function.
#     :returns: The attribute dictionary, or None if not found.
# =======================================================================
# def get_user_attribute_by_id (inst_url: str, inst_dev_token: str, attribute_id: str, log_func: LogFunc) -> Optional[Dict[str, Any]]:
#     print(f"STUB: Getting user attribute by ID {attribute_id} from {inst_url}")
#     return None
# # END def get_user_attribute_by_id

# =======================================================================
# USER MODIFICATION FUNCTIONS
# =======================================================================

# =======================================================================
# SAVES (CREATES OR UPDATES) A USER
#     Stubs out functionality to create or update a user.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param user_obj: The domo_objects.User object (dataclass instance) to be saved.
#     :param log_func: Pre-bound logging function.
#     :returns: The string ID of the saved user, or None on failure.
# =======================================================================
# def save_user (inst_url: str, inst_dev_token: str, user_obj: domo_objects.User, log_func: LogFunc) -> Optional[str]:
#     print(f"STUB: Saving user {user_obj.email_address} to {inst_url}")
#     return user_obj.id
# # END def save_user

# =======================================================================
# SAVES (CREATES OR UPDATES) A USER ATTRIBUTE
#     Stubs out functionality to create or update a user attribute.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param attribute_obj: The Attribute object (dictionary) to be saved.
#     :param log_func: Pre-bound logging function.
#     :returns: The key (string) of the saved attribute, or None on failure.
# =======================================================================
# def save_user_attribute (inst_url: str, inst_dev_token: str, attribute_obj: Dict[str, Any], log_func: LogFunc) -> Optional[str]:
#     print(f"STUB: Saving user attribute {attribute_obj.get('key')} to {inst_url}")
#     return attribute_obj.get('key')
# # END def save_user_attribute

# =======================================================================
# DELETES A USER BY ID
#     Stubs out functionality to delete a user.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param user_id: The string ID of the user to delete.
#     :param log_func: Pre-bound logging function.
#     :returns: True on success, False on failure.
# =======================================================================
# def delete_user (inst_url: str, inst_dev_token: str, user_id: str, log_func: LogFunc) -> bool:
#     print(f"STUB: Deleting user {user_id} from {inst_url}")
#     return True
# # END def delete_user


# =======================================================================
# PRIVATE API RETRIEVAL FUNCTIONS
# =======================================================================

# =======================================================================
# PRIVATE: REMAPS USER DICTIONARIES KEYED BY EMAIL ADDRESS
#     (PRIVATE) Takes a map of users keyed by ID and remaps them keyed by emailAddress.
    
#     :param user_id_map: Dictionary of domo_objects.User objects keyed by User ID.
#     :returns: Dictionary mapping email address (str) to the domo_objects.User object.
# =======================================================================
def _get_user_email_map (user_id_map: Dict[str, Any], log_func: LogFunc) -> Dict[str, Any]:

    log_func('_______________ _get_user_email_map()')
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects

    user_email_map: Dict[str, domo_objects.User] = {}
    for user_id, user_details in user_id_map.items():
        # START for user_id, user_details in user_id_map.items()
        user_email_map[user_details.email_address] = user_details
        # END for user_id, user_details in user_id_map.items()

    log_func('_______________ END _get_user_email_map()')

    return user_email_map
# END def _get_user_email_map

# =======================================================================
# PRIVATE: RETRIEVES A LIST OF RAW USER ATTRIBUTE METADATA KEYS
#     (PRIVATE) Retrieves a list of all raw user attribute metadata keys (properties) from a Domo instance.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :returns: A list of raw attribute metadata dictionaries.
# =======================================================================
def _get_instance_attributes (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Dict[str, Any]]:

    log_func(f'_______ _get_instance_attributes({inst_url})')
    
    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http

    api_url = f'https://{inst_url}.domo.com/api/user/v1/properties/meta/keys?issuerTypes=idp,domo-defined,customer-defined'
    
    # 1. Make API request
    attrs_res = edao_http.get(api_url, inst_dev_token, log_func)

    log_func('_______ END _get_instance_attributes()')

    return attrs_res
    
# END def _get_instance_attributes


# =======================================================================
# PRIVATE: RETRIEVES ALL USERS VIA PAGINATED SEARCH API
#     (PRIVATE) Searches and retrieves all users from an instance, including custom attributes 
#     from the provided SYNC_ATTRS map.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.

#     :returns: A list of raw user dictionaries.
# =======================================================================
def _get_instance_users_search (inst_url: str, inst_dev_token: str, log_func: LogFunc, sync_attrs: Any) -> List[Dict[str, Any]]:

    log_func(f'_______ _get_instance_users_search({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http

    # --- Step 1: Determine attributes to request ---
    # Call the PUBLIC attribute getter
    inst_attrs_map = get_all_instance_user_attributes(inst_url, inst_dev_token, log_func)
    
    attrs = []

    # Loop through the keys of the attributes map and populate the attrs list
    for attr_key in inst_attrs_map.keys():
        attrs.append(attr_key)

    # # Build the list of attributes that exist in the instance or are Domo-defined defaults
    # for attr_key, attr_details in sync_attrs.items():
    #     if attr_key in inst_attrs_map or attr_details.get("keyspace") == "domo-defined":
    #         attrs.append(attr_key)
    #     # END if attr_key in inst_attrs_map or attr_details.get("keyspace") == "domo-defined"
    # # END for attr_key, attr_details in sync_attrs.items()

    # --- Step 2: Paginate through users ---
                        
    api_url = f'https://{inst_url}.domo.com/api/identity/v1/users/search'    
    
    inst_user = []
    total = 100000
    offset = 0
    limit = 100
    
    while offset < total:
        # START while offset < total
        
        # Define the search body for the current page
        body = {
            "showCount": "true",
            "count": "false",
            "includeDeleted": "false",
            "includeSupport": "false",
            "limit": limit,
            "offset": offset,
            "sort": {
                "field": "displayName",
                "order": "ASC"
            },
            "filters": [],
            "attributes": [],
            "parts": ["GROUPS"]
        }
        # END body definition

        # START try
        resp = edao_http.post(api_url, inst_dev_token, log_func, body)
    
        # Update total count based on API response
        count = resp.get("count", 0)
        total = count
        page_users = resp.get("users", [])

        # Append users and increment offset
        inst_user.extend(page_users)
        offset = offset + limit
            
    # END while offset < total
    
    log_func(f'_______ END _get_instance_users_search({inst_url})')

    return inst_user
# END def _get_instance_users_search


# =======================================================================
# PRIVATE: LOAD USER OBJECTS
#     (PRIVATE) Converts a json list to a List of User objects
    
#     :param json: json array of data
#     :param log_func: Pre-bound logging function.
#     :returns: A list of User objects.
# =======================================================================
# def _load_user_objects(log_func: LogFunc, json_array: Any) -> List[objects.User]:
#     """
#     Parses a list of raw JSON objects into a list of domo_objects.Role instances.
#     Skips individual objects that fail to load.
#     """
    
#     loaded_objects = [] # Renamed from 'objects' to avoid shadowing the module name
    
#     # 1. Validate the input array
#     if json_array is None:
#         log_func("WARN: Input json_array is None. Returning empty list.")
#         return []
        
#     if not isinstance(json_array, list):
#         msg = f"CRITICAL: Input json_array must be a list, got {type(json_array).__name__}."
#         log_func(msg)
#         raise TypeError(msg)

#     # 2. Iterate through the array
#     for i, json_item in enumerate(json_array):
#         try:
#             # 3. Load individual object
#             obj = _load_user_object(log_func, json_item)
            
#             # Use .append() for Python lists (not .add)
#             loaded_objects.append(obj)
            
#         except (ValueError, RuntimeError) as e:
#             # 4. Handle known errors from the single object loader
#             log_func(f"ERROR: Failed to load object at index {i}. Skipping. Details: {e}")
#             continue
            
#         except Exception as e:
#             # 5. Handle unexpected errors
#             log_func(f"CRITICAL: Unexpected error loading object at index {i}: {e}")
#             continue

#     return loaded_objects
# # END def _load_user_objects()

# # =======================================================================
# # PRIVATE: LOAD USER OBJECT
# #     (PRIVATE) Converts a json obj to a User object
    
# #     :param json: json of data
# #     :param log_func: Pre-bound logging function.
# #     :returns: A single User object.
# # =======================================================================
# def _load_user_object(log_func: LogFunc, json: Any) -> domo_objects.User:
#     """
#     Parses raw JSON into an domo_objects.User instance. 
#     Raises an error if JSON is missing or if object creation fails.
#     """

#     # 1. Check if JSON is None or empty
#     if not json:
#         msg = "CRITICAL: Input JSON for _load_user_object is None or empty."
#         log_func(msg)
#         raise ValueError(msg)

#     try:
#         # 2. Attempt to create the User object
#         return domo_objects.User(
#             id=str(json.get('id', '')),
#             email_address=json.get('emailAddress', ''),
#             name=json.get('displayName'), # Owner base class name maps to displayName
#             type='USER',
#             user_name=json.get('userName'),
#             role_id=str(json.get('roleId')),
#             last_activity=json.get('lastActivity'),
#             groups=groups_list,
#             attributes=u_attrs_map
#         )    
    
#     except Exception as e:
#         # 3. Catch and re-raise errors during object creation
#         msg = f"CRITICAL: Failed to instantiate domo_objects.User. Error: {e}"
#         log_func(msg)
#         # Re-raise as a runtime error so the calling script knows it failed
#         raise RuntimeError(msg) from e
        
# # END def _load_user_object() -> domo_objects.User:    

# =======================================================================
# PRIVATE: LOAD USER OBJECTS
#     (PRIVATE) Converts a json list to a List of User objects
# =======================================================================
def _load_user_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.User instances.
    Skips individual objects that fail to load.
    """
    
    loaded_objects = [] 
    
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
            # FIX: Changed from _load_role_object to _load_user_object
            obj = _load_user_object(log_func, json_item)
            
            loaded_objects.append(obj)
            
        except (ValueError, RuntimeError) as e:
            log_func(f"ERROR: Failed to load object at index {i}. Skipping. Details: {e}")
            continue
            
        except Exception as e:
            log_func(f"CRITICAL: Unexpected error loading object at index {i}: {e}")
            continue

    return loaded_objects
# END def _load_user_objects()

# =======================================================================
# PRIVATE: LOAD USER OBJECT
#     (PRIVATE) Converts a json obj to a User object
# =======================================================================
def _load_user_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.User instance. 
    Raises an error if JSON is missing or if object creation fails.
    """
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_user_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # --- FIX: LOGIC MOVED HERE FROM MAIN FUNCTION ---
        
        # Process Custom attributes into Dict[str, List[str]] format
        u_attrs_map: Dict[str, List[str]] = {}
        if "attributes" in json:
            u_attrs = json['attributes']            
            for a in u_attrs:
                key = a.get("key")
                values = a.get("values", [])
                if key: u_attrs_map[key] = values

        # Process Groups
        groups_list: List[str] = []
        if "groups" in json:
            for g in json['groups']:
                if g.get("name"): groups_list.append(g["name"])
        
        # 2. Attempt to create the User object
        return domo_objects.User(
            id=str(json.get('id', '')),
            email_address=json.get('emailAddress', ''),
            name=json.get('displayName'), 
            type='USER',
            user_name=json.get('userName'),
            role_id=str(json.get('roleId')),
            last_activity=json.get('lastActivity'),
            groups=groups_list,      # Now defined
            attributes=u_attrs_map   # Now defined
        )    
    
    except Exception as e:
        msg = f"CRITICAL: Failed to instantiate domo_objects.User. Error: {e}"
        log_func(msg)
        raise RuntimeError(msg) from e
        
# END def _load_user_object()