# dgov_automation_scripts
This repository hold all the Jupyter Workspaces Pythons scripts that are used to automate dgov processes and create dgov reports and 

I've noted your preference for **no space between the function name and the opening parenthesis `(`** in function calls. I will revert to the standard Python (PEP 8) style for function calls and function definitions going forward, ensuring no space is present.

Here is the updated set of instructions for your `README.md` to ensure correct formatting:


| File | Public Function Name(s) | Private Function Name(s) | Notes |
| :--- | :--- | :--- | :--- |
| **accounts.py** | `get_all_instance_accounts`, `get_account_by_id`, `save_account`, `delete_account` | `_get_accounts_pages`, `_get_accounts_page_search` | `_get_accounts_pages` listed twice in Private column has been corrected to one entry. |
| **groups.py** | `get_all_instance_groups`, `get_group_by_name`, `create_group`, `save_group`, `delete_group`, `save_group_attributes`, `save_group_owners`, `save_group_image` | *(None)* | New: get/save/delete functions stubbed out. |
| **datasets.py** | `get_all_instance_datasets`, `get_dataset_stats`, `get_dataset_by_name`, `get_dataset_by_id`, `get_dataset_permissions`, `share_dataset`, `unshare_dataset`, `create_dataset`, `save_dataset`, `delete_dataset` | `_get_datasets_page`, `_get_page_search` | New: get\_by\_id/save/delete functions stubbed out. |
| **roles.py** | `get_instance_role_grants`, `get_instance_roles`, `get_instance_roles_by_id`, `get_role_by_name`, `get_role_by_id`, `save_role`, `delete_role` | `_get_instance_roles` | New: get\_by\_name/id, save/delete functions stubbed out. |
| **logs.py** | `log`, `get_current_time` | *(None)* | All core logging functions are public. |
| **helpers.py** | `get_http_headers`, `dataframe_to_csv`, `array_to_csv` | *(None)* | All utility functions are public. |
| **users.py** | `get_instance_users`, `get_all_instance_user_attributes`, `get_instance_user_by_id`, `get_user_by_email`, `get_user_by_id`, `get_user_attribute_by_name`, `get_user_attribute_by_id`, `save_user`, `save_user_attribute`, `delete_user` | `_get_user_email_map`, `_get_instance_attributes`, `_get_instance_users_search` | New: specific get/save/delete functions stubbed out. |
| **sandbox.py** | `get_instance_repositories_map`, `get_repository_user_owners_array`, `get_repository_group_owners_array`, `save_sandbox_repo`, `commit_sandbox_repo`, `delete_sandbox_repositories_by_name` | `_get_instance_repositories_page`, `_get_invited_domains`, `_get_repository_owners`, `_get_repository_content_ids_string` | **Streamlined functions:** `get_instance_repositories_map` is the primary retrieval function. |

---

## 💻 Code Style Guidelines

All Python code in this repository must strictly adhere to the following formatting and structural rules to enhance readability and maintainability.

1.  **Block Terminator Format:** Every indented code block (including functions, loops, conditional statements, and exception handling blocks) must be immediately followed by a comment on its own line, formatted as:

    ```
    # END <BLOCK_TYPE> <IDENTIFIER>
    ```

    **NOTE:** The preceding `# START` block format (e.g., `# START if condition`) is strictly **forbidden** and must be removed from the code.

2.  **Block Types and Identifiers:**
      * **Functions (`def`)**: Use the function's full name as the identifier (e.g., `# END def my_function`).
      * **Loops (`for`, `while`)**: Use the loop's initial statement (e.g., `# END for user in users_list`).
      * **Conditionals (`if`, `elif`, `else`)**: Use the initial condition or the block type (e.g., `# END if condition`, `# END else`).
      * **Context Managers (`with`)**: Use the variable name bound by the `as` clause (e.g., `# END with open ("file.txt", "r") as f`).
      * **Exception Handling (`try`, `except`)**: Use the block type and optionally the exception being caught (e.g., `# END try`, `# END except Exception as e`).

3.  **Indentation Level:** The `# END` comment must be at the same indentation level as the statement that started the block.

4.  **Function Spacing (Definition):** When **defining** a function, a single space must be placed between the function's name and the opening parenthesis `(`.
      * **Example:** `def array_to_csv (array: List[List[Any]], cols: List[str]) -> str:`

5.  **Function Spacing (Call - Standard PEP 8):** When **calling** a function, **no space** must be placed between the function's name and the opening parenthesis `(`.
      * **Example:** `log_func('Starting function.')`

6.  **Function Header and Docstrings:** Every function must be immediately preceded by a three-line comment header, followed by a Python docstring in **Sphinx/reST style** documenting the purpose, parameters (`:param`), and return value (`:returns`).

      * **Header Format:**
        ```python
        # =======================================================================
        # FUNCTION DESCRIPTION IN ALL CAPS (e.g., CORE API RETRIEVAL)
        # =======================================================================
        ```

7.  **Function Visibility (Public vs. Private):**
    * **Public Functions:** Do **not** start with a leading underscore (`_`).
    * **Private Functions (Internal Helpers):** Must **start** with a single leading underscore (`_`).

8.  **Strict Parameter Order for Credentialed Functions:**
    * All functions that require instance credentials must start their parameter list with:
      `inst_name: str, inst_url: str, inst_dev_token: str, log_func: LogFunc, ...`

9.  **Function Grouping and Ordering:** Functions within each module must be ordered as follows:
    * **Public Functions** (Retrieval/Listing $\rightarrow$ Mapping/ID Retrieval $\rightarrow$ Modification/Creation $\rightarrow$ Deletion/Unsharing)
    * **Private Functions** (Grouped at the bottom, ordered by dependency/usage)

Would you like me to proceed with applying the block termination and documentation guidelines to the rest of the provided Python files?