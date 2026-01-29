# randstadenterprise_edao_libraries/http.py
import requests # <-- ADD THIS IMPORT
import json
from typing import Dict, Any, List, Optional, Callable

# Define custom types needed for function signatures
LogFunc = Callable[[str], None]

# In http.py
class DomoAPIError(Exception):
    """Custom exception raised for failed Domo API calls."""
    pass

# ... rest of http.py ...


def get_http_headers (inst_dev_token: str) -> Dict[str, str]:
# =======================================================================
# GENERATES STANDARD DOMO API HEADERS
# =======================================================================
    # START def get_http_headers
    """
    Generates the standard HTTP headers required for Domo's private APIs.
    
    :param inst_dev_token: The developer token for 'X-DOMO-Developer-Token'.
    :returns: Dictionary of standard HTTP headers.
    """
    return {
        'X-DOMO-Developer-Token': inst_dev_token,
        # 'X-DOMO-Authentication': 'null', 
        'Content-Type': 'application/json;charset=utf-8',
        'Accept': 'application/json, text/plain, */*'
    }
# END def get_http_headers

############################
# GET
############################
def get(api_url: str, inst_dev_token: str, log_func: LogFunc) -> Any:

    log_func(f'>>>>>> get URL {api_url}')
    
    try:
        # Assuming you've fixed this to use json=body for Domo API calls
        resp = requests.get(api_url, headers=get_http_headers(inst_dev_token), timeout=30)
        
        # Check status and raise HTTPError if 4xx or 5xx
        resp.raise_for_status() 
        
        # log_func(f">>>>>>>> HTTP get success {str(resp)}")    
        
        # IMPORTANT: Call .json() on the response object 'resp', not 'result'
        # Check for empty response body before calling .json()
        result = resp.json() if resp.text else {} 
        # log_func(f"_____________________ HTTP get {str(result)}") 
        
        return result
    # END try:
    except requests.exceptions.HTTPError as e:
        # 1. Try to read the JSON error body from the response object within the exception
        try:
            error_details = e.response.json()
            
            # 2. Extract the specific message field
            domo_message = error_details.get("message", "No specific error message found in response body.")
            
            # 3. Log the extracted message
            log_func(f"ERROR: Domo API responded with 400 Bad Request. Message: {domo_message}")
            
            # You can now reraise a new exception with the custom message if needed
            raise DomoAPIError(f"API Failed: {domo_message}") from e
        # END try:            
        except requests.exceptions.JSONDecodeError:
            # If the response body wasn't JSON (e.g., HTML or plain text)
            log_func(f"ERROR: HTTPError {e.response.status_code}. Response was not JSON.")
            raise e # Reraise the original HTTPError
        # END except requests.exceptions.JSONDecodeError:
    # END except requests.exceptions.HTTPError as e:
    except requests.exceptions.RequestException as e:
        # Handle general connection/timeout errors
        log_func(f"ERROR: Request failed: {e}")
        raise e
    # END except requests.exceptions.RequestException as e:

# END get():

############################
# POST
############################
def post(api_url: str, inst_dev_token: str, log_func: LogFunc, body: Any) -> Any:

    log_func(f'>>>>>> post URL {api_url}')
    
    try:
        # Assuming you've fixed this to use json=body for Domo API calls
        resp = requests.post(api_url, headers=get_http_headers(inst_dev_token), json=body, timeout=30)
        
        # Check status and raise HTTPError if 4xx or 5xx
        resp.raise_for_status() 
        
        # IMPORTANT: Call .json() on the response object 'resp', not 'result'
        result = resp.json() if resp.text else {}
        
        return result
    # END try:
    except requests.exceptions.HTTPError as e:
        # 1. Try to read the JSON error body from the response object within the exception
        try:
            error_details = e.response.json()
            
            # 2. Extract the specific message field
            domo_message = error_details.get("message", "No specific error message found in response body.")
            
            # 3. Log the extracted message
            log_func(f"ERROR: Domo API responded with 400 Bad Request. Message: {domo_message}")
            
            # You can now reraise a new exception with the custom message if needed
            raise DomoAPIError(f"API Failed: {domo_message}") from e
        # END try:            
        except requests.exceptions.JSONDecodeError:
            # If the response body wasn't JSON (e.g., HTML or plain text)
            log_func(f"ERROR: HTTPError {e.response.status_code}. Response was not JSON.")
            raise e # Reraise the original HTTPError
        # END except requests.exceptions.JSONDecodeError:
    # END except requests.exceptions.HTTPError as e:
    except requests.exceptions.RequestException as e:
        # Handle general connection/timeout errors
        log_func(f"ERROR: Request failed: {e}")
        raise e
    # END except requests.exceptions.RequestException as e:

# END post():

############################
# PUT
############################
def put(api_url: str, inst_dev_token: str, log_func: LogFunc, body: Any) -> Any:

    log_func(f'>>>>>> put URL {api_url}')
    
    try:
        # Assuming you've fixed this to use json=body for Domo API calls
        resp = requests.put(api_url, headers=get_http_headers(inst_dev_token), json=body, timeout=30)
        
        # Check status and raise HTTPError if 4xx or 5xx
        resp.raise_for_status() 
        
        # IMPORTANT: Call .json() on the response object 'resp', not 'result'
        result = resp.json() if resp.text else {}
        
        return result
    
    # END try:
    except requests.exceptions.HTTPError as e:
        # 1. Try to read the JSON error body from the response object within the exception
        try:
            error_details = e.response.json()
            
            # 2. Extract the specific message field
            domo_message = error_details.get("message", "No specific error message found in response body.")
            
            # 3. Log the extracted message
            log_func(f"ERROR: Domo API responded with 400 Bad Request. Message: {domo_message}")
            
            # You can now reraise a new exception with the custom message if needed
            raise DomoAPIError(f"API Failed: {domo_message}") from e
        # END try:            
        except requests.exceptions.JSONDecodeError:
            # If the response body wasn't JSON (e.g., HTML or plain text)
            log_func(f"ERROR: HTTPError {e.response.status_code}. Response was not JSON.")
            raise e # Reraise the original HTTPError
        # END except requests.exceptions.JSONDecodeError:
    # END except requests.exceptions.HTTPError as e:
    except requests.exceptions.RequestException as e:
        # Handle general connection/timeout errors
        log_func(f"ERROR: Request failed: {e}")
        raise e
    # END except requests.exceptions.RequestException as e:

# END put():


############################
# PATCH
############################
def patch(api_url: str, inst_dev_token: str, log_func: LogFunc, body: Any) -> Any:

    log_func(f'>>>>>> patch URL {api_url}')
    
    try:
        # Assuming you've fixed this to use json=body for Domo API calls
        resp = requests.patch(api_url, headers=get_http_headers(inst_dev_token), json=body, timeout=30)
        
        # Check status and raise HTTPError if 4xx or 5xx
        resp.raise_for_status() 
        
        
        # IMPORTANT: Call .json() on the response object 'resp', not 'result'
        result = resp.json() if resp.text else {}
        
        return result
    
    # END try:
    except requests.exceptions.HTTPError as e:
        # 1. Try to read the JSON error body from the response object within the exception
        try:
            error_details = e.response.json()
            
            # 2. Extract the specific message field
            domo_message = error_details.get("message", "No specific error message found in response body.")
            
            # 3. Log the extracted message
            log_func(f"ERROR: Domo API responded with 400 Bad Request. Message: {domo_message}")
            
            # You can now reraise a new exception with the custom message if needed
            raise DomoAPIError(f"API Failed: {domo_message}") from e
        # END try:            
        except requests.exceptions.JSONDecodeError:
            # If the response body wasn't JSON (e.g., HTML or plain text)
            log_func(f"ERROR: HTTPError {e.response.status_code}. Response was not JSON.")
            raise e # Reraise the original HTTPError
        # END except requests.exceptions.JSONDecodeError:
    # END except requests.exceptions.HTTPError as e:
    except requests.exceptions.RequestException as e:
        # Handle general connection/timeout errors
        log_func(f"ERROR: Request failed: {e}")
        raise e
    # END except requests.exceptions.RequestException as e:

# END patch():

############################
# DELETE
############################
def delete(api_url: str, inst_dev_token: str, log_func: LogFunc) -> Any:

    log_func(f'>>>>>> delete URL {api_url}')
    
    try:
        # Assuming you've fixed this to use json=body for Domo API calls
        resp = requests.delete(api_url, headers=get_http_headers(inst_dev_token), timeout=30)
        
        # Check status and raise HTTPError if 4xx or 5xx
        resp.raise_for_status() 
        
        # If successful, return the response object
        return resp 
    
    # END try:
    except requests.exceptions.HTTPError as e:
        # 1. Try to read the JSON error body from the response object within the exception
        try:
            error_details = e.response.json()
            
            # 2. Extract the specific message field
            domo_message = error_details.get("message", "No specific error message found in response body.")
            
            # 3. Log the extracted message
            log_func(f"ERROR: Domo API responded with 400 Bad Request. Message: {domo_message}")
            
            # You can now reraise a new exception with the custom message if needed
            raise DomoAPIError(f"API Failed: {domo_message}") from e
        # END try:            
        except requests.exceptions.JSONDecodeError:
            # If the response body wasn't JSON (e.g., HTML or plain text)
            log_func(f"ERROR: HTTPError {e.response.status_code}. Response was not JSON.")
            raise e # Reraise the original HTTPError
        # END except requests.exceptions.JSONDecodeError:
    # END except requests.exceptions.HTTPError as e:
    except requests.exceptions.RequestException as e:
        # Handle general connection/timeout errors
        log_func(f"ERROR: Request failed: {e}")
        raise e
    # END except requests.exceptions.RequestException as e:

# END delete():