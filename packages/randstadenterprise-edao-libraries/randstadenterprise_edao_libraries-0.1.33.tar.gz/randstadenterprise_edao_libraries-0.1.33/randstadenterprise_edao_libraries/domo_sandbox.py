# randstadenterprise_edao_libraries/sandbox.py
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
#     :returns: A single list containing all raw repository dictionary objects.
# =======================================================================
def get_instance_repositories (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Dict[str, Any]]:

    log_func(f'____ get_instance_repositories({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    
    all_repos: List[objects.SandboxRepository] = []
    
    owned_repos = get_instance_owned_repositories (inst_url, inst_dev_token, log_func)
    shared_repos = get_instance_shared_repositories (inst_url, inst_dev_token, log_func)
     
    all_repos.extend(owned_repos)
    all_repos.extend(shared_repos)

    log_func(f"_______ owned_repos: {str(len(owned_repos))}")
    log_func(f"_______ shared_repos: {str(len(shared_repos))}")
    log_func(f"_______ TOTAL REPOS: {str(len(all_repos))}")
    
    log_func(f"____ END get_instance_repositories: {inst_url}")
    
    return all_repos

# END def get_instance_repositories


# =======================================================================
#     Retrieves OWNED repositories
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :returns: A single list containing all raw repository dictionary objects.
# =======================================================================
def get_instance_owned_repositories (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Dict[str, Any]]:

    log_func(f'____ get_instance_owned_repositories({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    
    all_results = []
    limit = 50
    offset = 0
    result_size = limit # Initialize to ensure loop starts

    while result_size == limit:

        # Get the first page to determine the total count for pagination
        repo_page_results = _get_instance_repositories_page(inst_url, inst_dev_token, log_func, False, offset, limit)
        if repo_page_results is not None:

            page_results = repo_page_results.get("repositories", [])
        
            # 1. Update result_size to the count of items in the CURRENT page
            result_size = len(page_results) 
            
            if result_size > 0:
                # Add all items from the current page to the final list
                all_results.extend(page_results)

                # 2. Increment offset by the size of the current page
                offset += result_size 
            # END if result_size > 0:
        # END if repo_page_results is not None:            
        else:
            log_func(f"_______ NO REPOSITORIES FOUND or critical error at offset: {str(offset)}")
            break
        # END else
        
    # END while result_size == limit:
            
    log_func(f"_______ TOTAL OWNED REPOS: {str(len(all_results))}")

    all_objects: List[objects.SandboxRepository] = []
    all_objects = _load_repo_objects(log_func, all_results)
        
    log_func(f"____ END get_instance_owned_repositories: {inst_url}")
    
    return all_objects

# END def get_instance_owned_repositories


# =======================================================================
#     Retrieves OWNED repositories
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :returns: A single list containing all raw repository dictionary objects.
# =======================================================================
def get_instance_shared_repositories (inst_url: str, inst_dev_token: str, log_func: LogFunc) -> List[Dict[str, Any]]:

    log_func(f'____ get_instance_shared_repositories({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    
    all_results = []
    limit = 50
    offset = 0
    result_size = limit # Initialize to ensure loop starts

    while result_size == limit:

        # Get the first page to determine the total count for pagination
        repo_page_results = _get_instance_repositories_page(inst_url, inst_dev_token, log_func, True, offset, limit)
        if repo_page_results is not None:

            page_results = repo_page_results.get("repositories", [])
        
            # 1. Update result_size to the count of items in the CURRENT page
            result_size = len(page_results) 
            
            if result_size > 0:
                # Add all items from the current page to the final list
                all_results.extend(page_results)

                # 2. Increment offset by the size of the current page
                offset += result_size 
            # END if result_size > 0:
        # END if repo_page_results is not None:            
        else:
            log_func(f"_______ NO REPOSITORIES FOUND or critical error at offset: {str(offset)}")
            break
        # END else
        
    # END while result_size == limit:
            
    log_func(f"_______ TOTAL SHARED REPOS: {str(len(all_results))}")

    all_objects: List[objects.SandboxRepository] = []
    all_objects = _load_repo_objects(log_func, all_results)
        
    log_func(f"____ END get_instance_shared_repositories: {inst_url}")
    
    return all_objects

# END def get_instance_shared_repositories

# =======================================================================
#     Retrieves a repository by id
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param repo_id: The exact id of the repo to find.
#     :returns: A single repository object.
# =======================================================================
def get_repository_by_id (inst_url: str, inst_dev_token: str, log_func: LogFunc, repo_id: str) -> Any:

    log_func(f'____ get_repository_by_id({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f"https://{inst_url}.domo.com/api/version/v1/repositories/{repo_id}"

    resp = edao_http.get(api_url, inst_dev_token, log_func)
    
    repo_object = _load_repo_object(log_func, resp)
        
    log_func(f"____ END get_repository_by_id: {inst_url}")
    
    return repo_object

# END def get_repository_by_id

# =======================================================================
#     Retrieves a repository by name
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param repo_name: The exact name of the repo to find.
#     :returns: A single repository object. This will return the first repo return with the provided name
# =======================================================================
def get_repository_by_name (inst_url: str, inst_dev_token: str, log_func: LogFunc, repo_name: str, shared_repos: bool) -> Any:

    log_func(f'____ get_repository_by_name({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f"https://{inst_url}.domo.com/api/version/v1/repositories/search"
    
    sort = "started" if shared_repos else "lastCommit"

    body = {
        "query": {
            "offset": 0,
            "limit": 50,
            "fieldSearchMap": {
                "repositoryName" : repo_name
            },
            "sort": sort,
            "order": "desc",
            # "filters": {
            #     "userId": None
            # },
            "dateFilters": {}
        },
        "shared": shared_repos
    }    

    resp = edao_http.post(api_url, inst_dev_token, log_func, body)
    
    repos = resp.get("repositories", [])
    
    repo_object = {}
    
    if len(repos) > 0:
        repo_object = _load_repo_object(log_func, repos[0])
        
    log_func(f"____ END get_repository_by_name: {inst_url}")
    
    return repo_object

# END def get_repository_by_name


# =======================================================================
#     Retrieves the committed versions of a repository
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param repo_id: The exact id of the repo to retrieve the commits.
#     :returns: A single list containing all raw repository commit objects.
# =======================================================================
def get_repository_commits (inst_url: str, inst_dev_token: str, log_func: LogFunc, repo_id: str) -> Any:

    log_func(f'____ get_repository_commits({str(inst_url)}, {str(repo_id)})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 
    
    api_url = f"https://{inst_url}.domo.com/api/version/v1/repositories/{str(repo_id)}/commits"

    resp = edao_http.get(api_url, inst_dev_token, log_func)
    
    commits = resp.get("commits", [])
    
    commit_objects = {}
    
    if len(commits) > 0:
        commit_objects = _load_repo_commit_objects(log_func, repo_id, commits)
        
    log_func(f'____ END get_repository_commits({str(inst_url)}, {str(repo_id)})')
    
    return commit_objects

# END def get_repository_commits

# =======================================================================
#     Promote Repository
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param last_promotion: The last promotion of the sandbox repository.
#     :returns: The string ID of the promoted repository, or None on failure.
# =======================================================================
def promote_repository (inst_url: str, inst_dev_token: str, log_func: LogFunc, last_promotion: Any) -> Optional[Any]:

    log_func(f'____ promote_repository({inst_url})')  

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 
    
    deploy = last_promotion.SandboxDeployment
    repo = deploy.SandboxRepository
    last_promotion_request = last_promotion.promotion_request

    body = {
                "commitId": last_promotion.commit_id,
                "mapping": last_promotion_request.mapping,
                "pusherEventId":  last_promotion.pusher_event_id,
                "approvalId": ""
            }
    
    api_url = f"https://{inst_url}.domo.com/api/version/v1/repositories/{repo.id}/deployments/{deploy.id}/promotions"
    
    resp = edao_http.post(api_url, inst_dev_token, log_func, body)
    
    promotion = _load_promotion_object(log_func, resp)
    promotion.repository_id = repo.id
    promotion.SandboxDeployment = deploy
        
    log_func(f"____ END promote_repository: {inst_url}")
    
    return promotion  

# END def promote_repository

# =======================================================================
#     Retrieves a repository promote logs
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param promotion: The promotion object to get the logs
#     :returns: A single repository object. This will return the first repo return with the provided name
# =======================================================================
def get_repository_promotion_logs (inst_url: str, inst_dev_token: str, log_func: LogFunc, promotion: Any) -> List[Any]:

    log_func(f'____ get_repository_latest_promotion_logs({inst_url})')

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 
    from . import edao_http 
    
    deploy = promotion.SandboxDeployment
    repo = deploy.SandboxRepository
    # promotion_request = promotion.promotion_request
    
    api_url = f"https://{inst_url}.domo.com/api/version/v1/repositories/{repo.id}/deployments/{deploy.id}/promotions/{promotion.id}/events/search"
    
    body = {
              "offset": 0,
              "limit": 500,
              "filters": {
                "contentId": [],
                "contentType": [],
                "status": [],
                "action": [],
                "contentName": []
              },
              "fieldSearchMap": {},
              "sort": "completed",
              "order": "desc",
              "searchDistinct": False,
              "dateFilters": {}
            }  

    resp = edao_http.post(api_url, inst_dev_token, log_func, body)
    
    logs = resp.get("contentEvents", [])
    
    repo_logs = []
    
    if len(logs) > 0:
        repo_logs = _load_repo_promote_log_objects(log_func, logs, promotion)
        
    log_func(f"____ END get_repository_latest_promotion_logs: {inst_url}")
    
    return repo_logs

# END def get_repository_latest_promotion_logs


# =======================================================================
# MAPPING AND ENRICHMENT FUNCTIONS (GET_BY_ID/MAP)
# =======================================================================
# def get_instance_repositories_map (
#     inst_url: str, inst_dev_token: str, inst_name: str, shared_repos: bool, log_func: LogFunc
# ) -> Dict[str, Dict[str, Any]]:
#     """
#     Retrieves all repositories (owned or shared), enriches them with owner/domain information,
#     and returns them mapped by Repository ID.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param inst_name: The friendly name of the Domo instance.
#     :param shared_repos: Flag to retrieve shared (True) or owned (False) repositories.
#     :param log_func: Pre-bound logging function.
#     :returns: Dictionary mapping Repository ID (str) to the enriched repository dictionary.
#     """

#     log_func(f'_______________ get_instance_repositories_map(shared: {shared_repos}): Starting enrichment.')

#     # 1. Get all repositories
#     inst_repos = get_all_instance_repositories(inst_url, inst_dev_token, shared_repos, log_func)
#     repos_map = {}

#     for repo in inst_repos:
#         # START for repo in inst_repos
#         repo_id = str(repo.get('id'))
        
#         if not repo_id:
#             # START if not repo_id
#             log_func(f"WARN: Skipping repository with no ID.")
#             continue
#             # END if not repo_id
            
#         invited_domains = []
#         repo_owners = {}
        
#         # Determine if the repository is owned or a shared deployment
#         if not shared_repos:
#             # START if not shared_repos
#             # Owned repositories allow sharing with other domains and have direct owners
#             invited_domains = _get_invited_domains(inst_url, inst_dev_token, repo_id, log_func) 
#             repo_owners = _get_repository_owners(inst_url, inst_dev_token, shared_repos, repo_id, None, log_func)
#             # END if not shared_repos
#         else:                     
#             # START else
#             # Shared repositories (deployments) have owners tied to the deployment
#             deploy_id = None
#             if "deployments" in repo and len(repo["deployments"]) > 0:
#                 # START if "deployments" in repo and len(repo["deployments"]) > 0
#                 deploy = repo["deployments"][0]
#                 deploy_id = deploy.get("id")
#                 # END if "deployments" in repo and len(repo["deployments"]) > 0
                
#             if deploy_id:
#                 # START if deploy_id
#                 # Owners are requested using the specific deployment ID
#                 repo_owners = _get_repository_owners(inst_url, inst_dev_token, shared_repos, repo_id, deploy_id, log_func) 
#                 # END if deploy_id
#             else:
#                 # START else
#                 log_func(f"WARN (Repo ID: {repo_id}): Shared repository found with no deployment ID.")
#                 # END else

#             # END else

#         # Inject enrichment data into the main repo dictionary
#         repo["invited_domains"] = invited_domains
#         repo["repo_owners"] = repo_owners
#         repo["instance_name"] = inst_name 
        
#         repos_map[repo_id] = repo
#         # END for repo in inst_repos
            
#     log_func('_______________ END get_instance_repositories_map()')

#     return repos_map


def get_repository_user_owners_array (
    repo: Dict[str, Any], inst_users_map: Dict[str, Dict[str, Any]], log_func: LogFunc
) -> List[Dict[str, Union[str, int]]]:
    """
    Extracts user ownership details from a repository dictionary, enriching with 
    display name and email from the provided user map.
    
    :param repo: The enriched repository dictionary (must contain 'repo_owners').
    :param inst_users_map: The full map of users keyed by User ID (str).
    :param log_func: Pre-bound logging function.
    :returns: A list of dictionaries, each describing a user owner.
    """
    
    user_owners = []
    
    if "repo_owners" in repo:
        # START if "repo_owners" in repo
        repo_owners = repo["repo_owners"]
        if "userPermissions" in repo_owners and isinstance(repo_owners["userPermissions"], dict):
            # START if "userPermissions" in repo_owners and isinstance(repo_owners["userPermissions"], dict)
            # Key is User ID (str), Value is access type (e.g., 'OWNER', 'COMMIT')
            for u_id, own_typ in repo_owners["userPermissions"].items():
                # START for u_id, own_typ in repo_owners["userPermissions"].items()
                u_id_str = str(u_id)
                u_name = u_id_str
                u_email = "N/A"
                
                # Lookup user details for enrichment
                if u_id_str in inst_users_map:
                    # START if u_id_str in inst_users_map
                    usr = inst_users_map[u_id_str]
                    u_name = usr.get("displayName", u_id_str)
                    u_email = usr.get("emailAddress", "N/A")
                    # END if u_id_str in inst_users_map
                
                user_owners.append({
                    "id": u_id_str,
                    "name": u_name,
                    "email": u_email,
                    "owner_access": own_typ
                })
                # END for u_id, own_typ in repo_owners["userPermissions"].items()
            # END if "userPermissions" in repo_owners and isinstance(repo_owners["userPermissions"], dict)
        # END if "repo_owners" in repo

    return user_owners


def get_repository_group_owners_array (
    repo: Dict[str, Any], inst_groups_map: Dict[str, Dict[str, Any]], log_func: LogFunc
) -> List[Dict[str, Union[str, int]]]:
    """
    Extracts group ownership details from a repository dictionary, enriching with 
    group name from the provided group map.
    
    :param repo: The enriched repository dictionary (must contain 'repo_owners').
    :param inst_groups_map: The full map of groups keyed by Group ID (str).
    :param log_func: Pre-bound logging function.
    :returns: A list of dictionaries, each describing a group owner.
    """

    group_owners = []
    
    if "repo_owners" in repo:
        # START if "repo_owners" in repo
        repo_owners = repo["repo_owners"]
        if "groupPermissions" in repo_owners and isinstance(repo_owners["groupPermissions"], dict):
            # START if "groupPermissions" in repo_owners and isinstance(repo_owners["groupPermissions"], dict)
            # Key is Group ID (str), Value is access type (e.g., 'OWNER', 'COMMIT')
            for g_id, own_typ in repo_owners["groupPermissions"].items():
                # START for g_id, own_typ in repo_owners["groupPermissions"].items()
                g_id_str = str(g_id)
                g_name = g_id_str
                
                # Lookup group details for enrichment (assuming the provided map is keyed by ID)
                if g_id_str in inst_groups_map:
                    # START if g_id_str in inst_groups_map
                    grp = inst_groups_map[g_id_str]
                    g_name = grp.get("name", g_id_str)
                    # END if g_id_str in inst_groups_map
                
                group_owners.append({
                    "id": g_id_str,
                    "name": g_name,
                    "owner_access": own_typ
                })
                # END for g_id, own_typ in repo_owners["groupPermissions"].items()
            # END if "groupPermissions" in repo_owners and isinstance(repo_owners["groupPermissions"], dict)
        # END if "repo_owners" in repo

    return group_owners

# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================
# =======================================================================

# =======================================================================
# PRIVATE: LOAD REPOSITORY OBJECTS
#     (PRIVATE) Create a list of REPOSITORY objects from a json list of objects.
    
#     :param log_func: Pre-bound logging function.
#     :param json_array: json array of dataset data
#     :returns: A list of SandboxRepository objects.
# =======================================================================
def _load_repo_objects(log_func: LogFunc, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.SandboxRepository instances.
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
            obj = _load_repo_object(log_func, json_item)
            
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
# END def _load_repo_objects

# =======================================================================
# PRIVATE: LOAD REPOSITORY OBJECT
#     (PRIVATE) Create a REPOSITORY object from a json object.
    
#     :param log_func: Pre-bound logging function.
#     :param json: json of repository data
#     :returns: A single SandboxRepository object.
# =======================================================================
def _load_repo_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.SandboxRepository instance. 
    Raises an error if JSON is missing or if object creation fails.
    """

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_repo_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the SandboxRepository object
        return domo_objects.SandboxRepository (
            id=json.get('id', ''),
            name=json.get('name', ''),
            domain=json.get('domain', ''),
            repo_type=json.get('type', ''),
            user_id=json.get('userId', ''),
            access_count=json.get('accessCount', ''),

            # Now fields with defaults
            repository_content=json.get('repositoryContent', {}),
            created=json.get('created', ''),
            updated=json.get('updated', ''),
            seeded=json.get('seeded', ''),
            last_commit=json.get('lastCommit', {}),
            permission=json.get('permission', ''),
            deployments=json.get('deployments', ''),
            commits=None
        )        
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.SandboxRepository. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_repo_object(log_func: LogFunc, json: Any) -> domo_objects.SandboxRepository:    


# =======================================================================
# PRIVATE: LOAD PROMOTION OBJECT
#     (PRIVATE) Create a SandboxPromotion object from a json object.
    
#     :param log_func: Pre-bound logging function.
#     :param json: json of promotion data
#     :returns: A single SandboxPromotion object.
# =======================================================================
def _load_promotion_object(log_func: LogFunc, json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.SandboxPromotion instance. 
    Raises an error if JSON is missing or if object creation fails.
    """
    
    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_promotion_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the SandboxPromotion object
        
        return domo_objects.SandboxPromotion (
                        deployment=None,
                        id=json.get('id', ''),
                        deployment_id=json.get('deploymentId', ''),
                        commit_id=json.get('commitId', ''),
                        repository_id=json.get('repositoryId', ''),
                        user_id=json.get('userId', ''),
                        commit_name=json.get('commitName', ''),
                        repository_name=json.get('repositoryName', ''),
                        started=json.get('started', ''),
                        completed=json.get('completed', ''),
                        status=json.get('status', ''),
                        pusher_event_id=json.get('pusherEventId', ''),
            
                        approval_id=json.get('promotionRequest', {}).get('approvalId', ''),
            
                        promotion_request=json.get('promotionRequest', {}),
                        promotion_result=json.get('promotionResult', {})
                    )         
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.SandboxPromotion. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_promotion_object(log_func: LogFunc, json: Any) -> domo_objects.SandboxPromotion:    


# =======================================================================
# PRIVATE: LOAD REPOSITORY PROMOTE LOG OBJECT
#     (PRIVATE) Create a REPOSITORY PROMOTE LOG object from a json object.
    
#     :param log_func: Pre-bound logging function.
#     :param json: json of repository promote log data
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_repo_promote_log_objects(log_func: LogFunc, json_array: Any, promotion:Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.SandboxPromotionLog instances.
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
            obj = _load_repo_promote_log_object(log_func, json_item, promotion)
            
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
# END def _load_repo_promote_log_objects

# =======================================================================
# PRIVATE: LOAD REPOSITORY PROMOTE LOG OBJECT
#     (PRIVATE) Create a REPOSITORY PROMOTE LOG object from a json object.
    
#     :param log_func: Pre-bound logging function.
#     :param json: json of repository promote log data
#     :returns: A list of dataset dictionary objects.
# =======================================================================
def _load_repo_promote_log_object(log_func: LogFunc, json: Any, promotion:Any) -> Any:
    """
    Parses raw JSON into an domo_objects.SandboxPromotionLog instance. 
    Raises an error if JSON is missing or if object creation fails.
    """

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_repo_promote_log_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the SandboxPromotionLog object
        return domo_objects.SandboxPromotionLog (
            promotion=promotion,
            log_id=json.get('id', ''),
            event_type=json.get('eventType', ''),
            event_id=json.get('eventId', ''),
            content_id=json.get('contentId', ''),
            content_name=json.get('contentName', ''),
            action=json.get('action', ''),
            content_type=json.get('contentType', ''),
            started=json.get('started', ''),
            completed=json.get('completed', ''),
            level=json.get('level', ''),
        )       
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.SandboxPromotionLog. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_repo_promote_log_object(log_func: LogFunc, json: Any) -> domo_objects.SandboxPromotionLog:    


# =======================================================================
# PRIVATE: LOAD REPOSITORY COMMITS OBJECTS
    
#     :param log_func: Pre-bound logging function.
#     :param json: json of repository promote log data
#     :returns: A list of commit object.
# =======================================================================
def _load_repo_commit_objects(log_func: LogFunc, repo_id: str, json_array: Any) -> List[Any]:
    """
    Parses a list of raw JSON objects into a list of domo_objects.SandboxCommit instances.
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
            obj = _load_repo_commit_object(log_func, repo_id, json_item)
            
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
# END def _load_repo_commit_objects

# =======================================================================
# PRIVATE: LOAD REPOSITORY COMMIT LOG OBJECT
    
#     :param log_func: Pre-bound logging function.
#     :param json: json of sandbox commit data
#     :returns: A sandbox commit object.
# =======================================================================
def _load_repo_commit_object(log_func: LogFunc, repo_id:str , json: Any) -> Any:
    """
    Parses raw JSON into an domo_objects.SandboxCommit instance. 
    Raises an error if JSON is missing or if object creation fails.
    """

    # ADD IMPORT HERE (Lazy Import)
    from . import domo_objects 

    # 1. Check if JSON is None or empty
    if not json:
        msg = "CRITICAL: Input JSON for _load_repo_commit_object is None or empty."
        log_func(msg)
        raise ValueError(msg)

    try:
        # 2. Attempt to create the SandboxCommit object
        return domo_objects.SandboxCommit (
            repo_id=repo_id,
            commit_id=json.get('id', ''),
            name=json.get('name', ''),
            hidden=json.get('hidden', ''),
            summary=json.get('summary', ''),
            path=json.get('path', ''),
            status=json.get('status', ''),
        )       
    
    except Exception as e:
        # 3. Catch and re-raise errors during object creation
        msg = f"CRITICAL: Failed to instantiate domo_objects.SandboxCommit. Error: {e}"
        log_func(msg)
        # Re-raise as a runtime error so the calling script knows it failed
        raise RuntimeError(msg) from e
        
# END def _load_repo_commit_object(log_func: LogFunc, json: Any) -> domo_objects.SandboxCommit:    


# =======================================================================
# =======================================================================
# =======================================================================
# PRIVATE API HELPER FUNCTIONS
# =======================================================================
# =======================================================================
# =======================================================================

# =======================================================================
# (PRIVATE HELPER) Fetches a single paginated result of repositories (owned or shared).
#     Used by get_all_instance_repositories.
    
#     :param inst_url: The Domo instance URL prefix.
#     :param inst_dev_token: The developer token.
#     :param log_func: Pre-bound logging function.
#     :param shared_repos: If True, retrieve shared repositories; False for owned.
#     :param offset: The starting index for pagination.
#     :param limit: The number of results to return.
#     :returns: The raw JSON response dictionary containing 'repositories' and 'pageContext', or an empty dict on error.
# =======================================================================
def _get_instance_repositories_page (inst_url: str, inst_dev_token: str, log_func: LogFunc, shared_repos: bool, offset: int, limit: int) -> Any:

    log_func(f'_______ _get_instance_repositories_page(shared: {str(shared_repos)}, offset: {str(offset)}, limit: {str(limit)})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/version/v1/repositories/search'
    
    sort = "started" if shared_repos else "lastCommit"

    body = {
        "query": {
            "offset": offset,
            "limit": limit,
            "fieldSearchMap": {},
            "sort": sort,
            "order": "desc",
            # "filters": {
            #     "userId": None
            # },
            "dateFilters": {}
        },
        "shared": shared_repos
    }
    
    page_result = edao_http.post(api_url, inst_dev_token, log_func, body)
        
    log_func('_______ END _get_instance_repositories_page()')

    return page_result
# END def _get_instance_repositories_page


def _get_invited_domains (inst_url: str, inst_dev_token: str, repo_id: str, log_func: LogFunc) -> List[Dict[str, str]]:
    """
    (PRIVATE HELPER) Fetches the list of domains an owned repository has been shared with.
    Used by get_instance_repositories_map for owned repositories.
    
    :param inst_url: The Domo instance URL prefix.
    :param inst_dev_token: The developer token.
    :param repo_id: The ID of the repository.
    :param log_func: Pre-bound logging function.
    :returns: A list of dictionaries, each containing 'repositoryId' and 'invitedDomain'.
    """

    log_func(f'____________________ _getInvitedDomains(repo_id: {repo_id})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    api_url = f'https://{inst_url}.domo.com/api/version/v1/repositories/{repo_id}/access'
    
    invited_domains_result = []
    
    try:
        # START try
        resp = edao_http.get(api_url, headers=helpers.get_http_headers(inst_dev_token), timeout=20)
        resp.raise_for_status() 
        
        invited_domains_json = resp.json()
        # Extract the 'accessList' array, ensuring it exists and is a list
        if "accessList" in invited_domains_json and isinstance(invited_domains_json["accessList"], list):
            # START if "accessList" in invited_domains_json and isinstance(invited_domains_json["accessList"], list)
            invited_domains_result = invited_domains_json["accessList"]
            # END if "accessList" in invited_domains_json and isinstance(invited_domains_json["accessList"], list)
            
        # END try
    except requests.exceptions.RequestException as e:
        # START except requests.exceptions.RequestException
        log_func(f"ERROR fetching invited domains (repo_id: {repo_id}): {type(e).__name__} - {e}")
        # END except requests.exceptions.RequestException
        
    log_func('____________________ END _getInvitedDomains()')

    return invited_domains_result
# END def _get_invited_domains


def _get_repository_owners (
    inst_url: str, inst_dev_token: str, shared_repos: bool, repo_id: str, deploy_id: Optional[str], log_func: LogFunc
) -> Dict[str, Any]:
    """
    (PRIVATE HELPER) Fetches user and group permissions for a repository (or deployment).
    Used by get_instance_repositories_map.
    
    :param inst_url: The Domo instance URL prefix.
    :param inst_dev_token: The developer token.
    :param shared_repos: If True, the permissions are for a shared deployment; False for an owned repo.
    :param repo_id: The ID of the repository.
    :param deploy_id: The deployment ID, required if shared_repos is True.
    :param log_func: Pre-bound logging function.
    :returns: A dictionary containing 'userPermissions' and 'groupPermissions', or an empty dict on error.
    """

    log_func(f'____________________ _getRepositoryOwners(repo_id: {repo_id}, deploy_id: {deploy_id})')

    # ADD IMPORT HERE (Lazy Import)
    from . import edao_http 

    # Construct the API URL based on whether it's an owned repo or a shared deployment
    if shared_repos and deploy_id:
        # START if shared_repos and deploy_id
        api_url = f'https://{inst_url}.domo.com/api/version/v1/repositories/{repo_id}/deployments/{deploy_id}/permissions'
        # END if shared_repos and deploy_id
    else:
        # START else
        api_url = f'https://{inst_url}.domo.com/api/version/v1/repositories/{repo_id}/permissions'
        # END else
    
    owners_result = {}
    
    resp = edao_http.get(api_url, headers=helpers.get_http_headers(inst_dev_token), timeout=20)
    resp.raise_for_status() 
    owners_result = resp.json()
        
    log_func('____________________ END _getRepositoryOwners()')

    return owners_result
# END def _get_repository_owners


def _get_repository_content_ids_string (
    repo: Dict[str, Any], content_key: str, log_func: LogFunc
) -> str:
    """
    (PRIVATE HELPER) Extracts a pipe-separated string of IDs for a specific content type 
    (e.g., 'pageIds', 'viewIds') from a repository object.
    
    :param repo: The repository dictionary object.
    :param content_key: The key within 'repositoryContent' (e.g., 'pageIds').
    :param log_func: Pre-bound logging function.
    :returns: Pipe-separated string of IDs, or an empty string.
    """
    
    # log_func(f'_______________ _get_repository_content_ids_string({content_key})')

    content_ids_str = ""
    
    if "repositoryContent" in repo:
        # START if "repositoryContent" in repo
        repository_content = repo["repositoryContent"]
        if content_key in repository_content:
            # START if content_key in repository_content
            id_list = repository_content[content_key]
            if isinstance(id_list, list):
                # START if isinstance(id_list, list)
                # Concatenate IDs with a pipe separator using a list comprehension
                content_ids_str = "|".join([str(id_val) for id_val in id_list])
                # END if isinstance(id_list, list)
            # END if content_key in repository_content
        # END if "repositoryContent" in repo

    # log_func(f'_______________ END _get_repository_content_ids_string({content_key})')
    return content_ids_str
# END def _get_repository_content_ids_string