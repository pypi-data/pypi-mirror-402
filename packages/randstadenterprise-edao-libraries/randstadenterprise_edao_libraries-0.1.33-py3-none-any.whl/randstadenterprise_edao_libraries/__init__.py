# randstadenterprise_edao_libraries/__init__.py

# 1. Base Utility Modules (Load First)
from . import edao_logs
from . import domo_objects
from . import edao_http
from . import edao_helpers

# 2. Logic Modules (Ordered by Dependency)
from . import domo_groups    # Independent
from . import domo_roles     # Independent API
from . import domo_datasets  # Depends on logs/helpers
from . import domo_users     # Depends on roles/groups
from . import domo_assets    # Depends on users (via ownership logic)
from . import domo_sandbox   # Depends on everything

__all__ = ['edao_logs', 'domo_objects', 'edao_http', 'edao_helpers', 'domo_groups', 'domo_roles', 'domo_users', 'domo_datasets', 'domo_assets', 'domo_sandbox']
__version__ = "0.1.33"

# In Terminal RUN in library_root
# cd library_root
# rm -rf dist
# pyhon -m build
# python -m twine upload dist/*

