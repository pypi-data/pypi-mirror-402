# objects.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# =======================================================================
# ABSTRACT OWNER BASE CLASS (FIXED: All core fields are now mandatory)
# =======================================================================

@dataclass
class Owner:
    """Abstract base class representing an entity (User or Group) that can own an object."""
    # These fields are REQUIRED for initialization and have NO defaults.
    id: str
    name: Optional[str] 
    type: Optional[str] 
# END class Owner

# =======================================================================
# INSTANCE CONFIGURATION OBJECTS
# =======================================================================

@dataclass
class Instance:
    """Represents a single Domo instance configuration record loaded from a control dataset."""
    
    # Core Identification
    Instance_Name: str
    Instance_URL: str
    Developer_Token: str
    
    # Secondary Identification and Attributes
    Developer_Token_User: Optional[str] = field(default=None)
    Instance_Abbreviation: Optional[str] = field(default=None)
    Client_Name: Optional[str] = field(default=None)
    Client_ID: Optional[str] = field(default=None)
    Client_Secret: Optional[str] = field(default=None)
    Environment: Optional[str] = field(default=None)
    Region: Optional[str] = field(default=None)
    Type: Optional[str] = field(default=None)
    Level: Optional[str] = field(default=None)
    Description: Optional[str] = field(default=None)
    Instance_Color: Optional[str] = field(default=None)
    Old_Instance: Optional[str] = field(default=None)

    # Sync and Status Flags
    Sync_Datasets_Owners: Optional[str] = field(default=None)
    Sync_User_Landing_Page: Optional[str] = field(default=None)
    Include_in_User_Activity: Optional[str] = field(default=None)
    Show_In_SSO_Portal: Optional[str] = field(default=None)
    Sync_Default_Roles: Optional[str] = field(default=None)
    Sync_Users: Optional[str] = field(default=None)
    Sync_Default_Groups: Optional[str] = field(default=None)
    
    # Dates and Ordering
    Load_Data_Date: Optional[str] = field(default=None)
    Build_Cards_Date: Optional[str] = field(default=None)
    Go_Live_Date: Optional[str] = field(default=None)
    Order: Optional[int] = field(default=None)
    
    # Login Configuration
    Randstad_Login: Optional[str] = field(default=None)
    Login_Type: Optional[str] = field(default=None)
    Client_Login: Optional[str] = field(default=None)
# END class Instance

# =======================================================================
# DOMO OBJECTS
# =======================================================================

@dataclass
class RoleGrant:
    """Represents a single authority (permission) granted to a role."""
    authority: str
    # title: str
    description: Optional[str] = field(default=None)
    role_ids: List[str] = field(default_factory=list)
# END class RoleGrant

@dataclass
class Role:
    """Represents a Domo Role, including its ID, name, and associated grants."""
    id: str
    name: str
    description: Optional[str] = field(default=None)
    is_default: Optional[bool] = field(default=None)
    # grants should be mapped by authority name for easy lookup
    grants: Dict[str, RoleGrant] = field(default_factory=dict)
# END class Role

@dataclass
class Account(Owner):
    """Represents a Domo Integration Account (Data Source Credentials)."""
    # Inherits: id, name, type (all mandatory)
    display_name: Optional[str] = field(default=None)
    entity_type: Optional[str] = field(default=None)
    data_provider_type: Optional[str] = field(default=None)
    valid: Optional[bool] = field(default=None)
    last_modified: Optional[str] = field(default=None)
    owners: List[Owner] = field(default_factory=list) # List of Owner objects
    dataset_count: Optional[int] = field(default=None)
# END class Account

@dataclass
class Group(Owner):
    """Represents a Domo Group."""
    # Inherits: id, name, type (all mandatory)
    # group_id: str
    # name: str
    group_type: str

    description: Optional[str] = field(default=None)
    owners: List[Owner] = field(default_factory=list)
    user_ids: List[str] = field(default_factory=list)    
    users: List[Any] = field(default_factory=list)    
    active: bool = field(default=True)
    created: str = field(default='')
    creator_id: str = field(default='')
    default: bool = field(default=False)
    guid: str = field(default='')
    hidden: bool = field(default=False)
    member_count: int = field(default=0)
    modified: str = field(default='')
    
# END class Group

@dataclass
class Dataset:
    """Represents a Domo DataSet."""
    id: str
    name: str
    
    description: Optional[str] = field(default=None)

    data_provider_name: Optional[str] = field(default=None)
    row_count: Optional[int] = field(default=None)
    column_count: Optional[int] = field(default=None)
    owners: List[Owner] = field(default_factory=list) # List of Owner objects
# END class Dataset

@dataclass
class DataDictionary:
    """Represents a Domo DataDictionary."""
    id: str
#     name: str
    
#     description: Optional[str] = field(default=None)

#     data_provider_name: Optional[str] = field(default=None)
#     row_count: Optional[int] = field(default=None)
#     column_count: Optional[int] = field(default=None)
#     owners: List[Owner] = field(default_factory=list) # List of Owner objects
# END class DataDictionary

@dataclass
class User(Owner):
    """Represents a Domo User."""
    # Inherits: id, name, type (all mandatory)
    
    # New mandatory field comes after all inherited mandatory fields.
    email_address: str
    
    # Now fields with defaults
    user_name: Optional[str] = field(default=None)
    role_id: Optional[str] = field(default=None)
    last_activity: Optional[str] = field(default=None)
    groups: List[str] = field(default_factory=list) # List of group IDs
    attributes: Dict[str, List[str]] = field(default_factory=dict) # Key -> List of values
# END class User

@dataclass
class SandboxRepository:
    """Represents a Domo SandboxRepository."""
    
    # New mandatory field comes after all inherited mandatory fields.
    id: str
    name: str
    domain:str
    repo_type:str
    
    # Now fields with defaults
    repositoryContent: Any = field(default=None)
    user_id: Optional[str] = field(default=None)
    access_count: Optional[str] = field(default=None)
    permission: Optional[str] = field(default=None)
    created: Optional[str] = field(default=None)
    updated: Optional[str] = field(default=None)
    seeded: Optional[str] = field(default=None)
    last_commit: Optional[Any] = field(default=None)
    
    deployments: Optional[List['SandboxDeployment']] = field(default=None)
    commits: Optional[List['SandboxCommit']] = field(default=None)
        
    def __init__(self, id, name, domain, repo_type, user_id, access_count, repository_content, created, updated, seeded, last_commit, permission, deployments: Any, commits: Any):
        
        self.id = id
        self.name = name
        self.domain = domain
        self.repo_type = repo_type
        self.user_id = user_id,
        self.access_count = access_count

        # Now fields with defaults
        self.repository_content = repository_content,
        self.created = created,
        self.updated = updated,
        self.seeded = seeded,
        self.last_commit = last_commit,
        self.permission = permission,
        
        if deployments is not None and len(deployments) > 0:
            self.deployments = []
            for d in deployments:
                d_obj = SandboxDeployment (
                        repo=self,
                        id=d.get('id', ''),
                        repo_id=d.get('repositoryId', ''),
                        domain=d.get('domain', ''),
                        name=d.get('name', ''),

                        # Now fields with defaults
                        is_source=d.get('isSource', ''),
                        user_id=d.get('userId', ''),
                        created=d.get('created', ''),
                        updated=d.get('updated', ''),

                        last_promotion=d.get('lastPromotion', {}),

                        permission=d.get('permission', '')
                    )     
                
                self.deployments.append(d_obj)
                
            # END for d in deployments:
        # END if deployments is not None and len(deployments) > 0:

        
        if commits is not None and len(commits) > 0:
            self.commits = []
            for c in commits:    
                c_obj = SandboxCommit (
                    repo_id=id,
                    repo=self,
                    commit_id=c.get('id', ''),
                    name=c.get('name', ''),
                    hidden=c.get('hidden', ''),
                    summary=c.get('summary', ''),
                    path=c.get('path', ''),
                    status=c.get('status', ''),
                )                   
                
                self.commits.append(c_obj)
                
            # END for c in commits:    
        # END if commits is not None and len(commits) > 0:
        
    # END def __init__(self, repo_id, name, domain, repo_type, userId, accessCount, repositoryContent, created, updated, seeded, lastCommit, permission):
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, SandboxRepository):
            return NotImplemented
        return self.id == other.id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.id)
    # END def __hash__(self):
        
# END class SandboxRepository

@dataclass
class SandboxDeployment:
    """Represents a Domo SandboxDeployment."""
    
    SandboxRepository: SandboxRepository

    # New mandatory field comes after all inherited mandatory fields.
    id: str
    repository_id: str
    name: str
    domain:str
    
    # Now fields with defaults
    user_id: Optional[str] = field(default=None)
    is_source: bool = field(default=None)
    permission: Optional[str] = field(default=None)
    created: Optional[str] = field(default=None)
    updated: Optional[str] = field(default=None)
    last_promotion: Optional['SandboxPromotion'] = field(default=None)
    
    def __init__(self, repo: SandboxRepository, id, repo_id, name, domain, user_id, is_source, created, updated, last_promotion, permission):
        
        self.SandboxRepository = repo
        
        self.id = id
        self.repository_id = repo_id
        self.name = name
        self.domain = domain
        
        # Now fields with defaults
        self.user_id = user_id
        self.is_source = is_source
        self.created = created
        self.updated = updated
        self.permission = permission
        
        self.last_promotion = SandboxPromotion (
                        deployment=self,
                        id=last_promotion.get('id', ''),
                        deployment_id=last_promotion.get('deploymentId', ''),
                        commit_id=last_promotion.get('commitId', ''),
                        repository_id=last_promotion.get('repositoryId', ''),
                        user_id=last_promotion.get('userId', ''),
                        commit_name=last_promotion.get('commitName', ''),
                        repository_name=last_promotion.get('repositoryName', ''),
                        started=last_promotion.get('started', ''),
                        completed=last_promotion.get('completed', ''),
                        status=last_promotion.get('status', ''),
                        pusher_event_id=last_promotion.get('pusherEventId', ''),
                        approval_id=last_promotion.get('approvalId', ''),
            
                        promotion_request=last_promotion.get('promotionRequest', {}),
                        promotion_result=last_promotion.get('promotionResult', {})
                    ) 
            
        
    # END def __init__(self, id, repo_id, name, domain, user_id, is_source, repositoryContent, created, updated, seeded, last_promotion, permission):
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, SandboxDeployment):
            return NotImplemented
        return self.id == other.id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.id)
    # END def __hash__(self):
        
# END class SandboxDeployment

@dataclass
class SandboxPromotionLog:
    """Represents a Domo SandboxPromotionLog."""
    
    SandboxPromotion: 'SandboxPromotion'

    # New mandatory field comes after all inherited mandatory fields.
    log_id: str
    
    event_type: str
    event_id: str
    content_id: str
    content_name: str
    action: str
    content_type: str
    started: str
    completed: str
    level: str
    
    def __init__(self, promotion:'SandboxPromotion', log_id, event_type, event_id, content_id, content_name, action, content_type, started, completed, level):

        self.SandboxPromotion = promotion
        self.log_id = log_id
        self.event_type = event_type
        self.event_id = event_id
        self.content_id = content_id
        self.content_name = content_name
        self.action = action
        self.content_type = content_type
        self.started = started
        self.completed = completed
        self.level = level
        
    # END def __init__():
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, SandboxPromotionLog):
            return NotImplemented
        return self.log_id == other.log_id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.log_id)
    # END def __hash__(self):
        
# END class SandboxPromotionRequest

@dataclass
class SandboxPromotion:
    """Represents a Domo SandboxPromotion."""
    
    SandboxDeployment: SandboxDeployment
    
    # New mandatory field comes after all inherited mandatory fields.
    id: str
    deployment_id: str
    commit_id: str
    repository_id: str
    user_id: str
    commit_name: str
    repository_name: str
    
    # Now fields with defaults
    started: Optional[str] = field(default=None)
    completed: Optional[str] = field(default=None)
    status: Optional[str] = field(default=None)
    pusher_event_id: Optional[str] = field(default=None)
    approval_id: Optional[str] = field(default=None)

    promotion_request: Optional[Any] = field(default=None)
    promotion_result: Optional[Any] = field(default=None)
    
    logs: Optional[List[SandboxPromotionLog]] = field(default=None)

    def __init__(self, deployment: SandboxDeployment, id, deployment_id, commit_id, repository_id, user_id, commit_name, repository_name, started, completed, status, pusher_event_id, approval_id, promotion_request, promotion_result):
        
        self.SandboxDeployment = deployment
        self.id = id
        self.deployment_id = deployment_id
        self.commit_id = commit_id
        self.repository_id = repository_id
        self.user_id = user_id
        self.commit_name = commit_name
        self.repository_name = repository_name
        
        # Now fields with defaults
        self.started = started
        self.completed = completed
        self.status = status
        self.pusher_event_id = pusher_event_id
        self.approval_id = approval_id
        self.promotion_result = promotion_result

        self.promotion_request = SandboxPromotionRequest (
                        promotion=self,
                        commit_id=promotion_request.get('commitId', ''),
                        pusher_event_id=promotion_request.get('pusherEventId', ''),
                        approval_id=promotion_request.get('approvalId', ''),
            
                        mapping=promotion_request.get('mapping', '')
                    )
        
    # END def __init__(self, id, deployment_id, commit_id, repository_id, commit_name, repository_name, started, completed, status, pusher_event_id, approval_id, promotion_request, promotion_result):
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, SandboxLastPromotion):
            return NotImplemented
        return self.id == other.id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.id)
    # END def __hash__(self):
        
# END class SandboxLastPromotion

@dataclass
class SandboxPromotionRequest:
    """Represents a Domo SandboxPromotionRequest."""
    
    SandboxPromotion: SandboxPromotion

    # New mandatory field comes after all inherited mandatory fields.
    commit_id: str
    mapping: Optional[Any] = field(default=None)
    pusher_event_id: Optional[str] = field(default=None)
    approval_id: Optional[str] = field(default=None)
    
    def __init__(self, promotion:SandboxPromotion, commit_id, mapping, pusher_event_id, approval_id):

        self.SandboxPromotion = promotion
        self.commit_id = commit_id
        self.mapping = mapping
        self.pusher_event_id = pusher_event_id
        self.approval_id = approval_id
        
    # END def __init__(self, commit_id, mapping, pusher_event_id, approval_id):
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, SandboxPromotionRequest):
            return NotImplemented
        return self.commit_id == other.commit_id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.commit_id)
    # END def __hash__(self):
        
# END class SandboxPromotionRequest

@dataclass
class SandboxCommit:
    """Represents a Domo SandboxCommit."""
    
    repo_id: str
            
    # New mandatory field comes after all inherited mandatory fields.
    commit_id: str
    name: str
    hidden: bool
    summary: str
    path: str
    status: str

    # Move optional fields (those with defaults) to the bottom
    created: Optional[str] = "N/A" 
    SandboxRepository: Optional[Any] = None
    
    def __init__(self, repo_id, commit_id, name, hidden, summary, path, status, created: Optional[str] = "N/A", repo: Optional[Any] = None):

        self.repo_id = repo_id
        self.commit_id = commit_id
        self.name = name
        self.hidden = hidden
        self.summary = summary
        self.path = path
        self.status = status

        self.created = created
        self.SandboxRepository = repo
        
    # END def __init__(self, commit_id, mapping, pusher_event_id, approval_id):
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, SandboxCommit):
            return NotImplemented
        return self.commit_id == other.commit_id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.commit_id)
    # END def __hash__(self):
        
# END class SandboxCommit


@dataclass
class Asset:
    """Represents a Domo App Asset."""
    
    # New mandatory field comes after all inherited mandatory fields.
    asset_id: str
    name: str
    owner: str
    
    created_by: str
    created_date: str
    updated_by: str
    updated_date: str

    latest_version: str
    owners: List[any]
    creator: any
    
    trusted: bool
    has_thumbnail: bool

    versions: List[any]
    
    # Now fields with defaults
    description: Optional[str] = field(default=None)
    deleted_date: Optional[str] = field(default=None)
    instances: List[any] = field(default_factory=list) # List of group IDs
    referencing_cards: List[any] = field(default_factory=list) # List of group IDs
       
    def __init__(self, asset_id, name, owner, created_by, created_date, updated_by, updated_date, description, versions, latest_version, instances, referencing_cards, owners, creator, deleted_date, trusted, has_thumbnail):
        
        self.asset_id = asset_id
        self.name = name
        self.owner = owner
        
        self.created_by = created_by
        self.created_date = created_date
        self.updated_by = updated_by
        self.updated_date = updated_date
        
        self.description = description

        self.latest_version = latest_version

        self.instances = instances
        self.referencing_cards = referencing_cards
        self.owners = owners
        self.creator = creator
        self.deleted_date = deleted_date
        self.trusted = trusted
        self.has_thumbnail = has_thumbnail
        
        if versions is not None and len(versions) > 0:
            self.versions = []
            for av in versions:
                av_obj = AssetVersion (
                        asset=self,
                        asset_version_id=av.get('id', ''),
                        design_id=av.get('designId', ''),
                        version=av.get('version', ''),
                        draft=av.get('draft', False),
                        trusted=av.get('trusted', False),
                        public_assets_enabled=av.get('publicAssetsEnabled', True),
                    
                        scopes=av.get('scopes', []),
                    
                        datasets_mapping=av.get('datasetsMapping', []),
                        collections_mapping=av.get('collectionsMapping', []),
                        accounts_mapping=av.get('databasesMapping', []),
                        actions_mapping=av.get('accountsMapping', []),
                        workflows_mapping=av.get('actionsMapping', []),
                        packages_mapping=av.get('packagesMapping', []),
                    
                        size_width=av.get('size', {'width':5.0,'height':5.0}).get('width', 5.0),
                        size_height=av.get('size', {'width':5.0,'height':5.0}).get('height', 5.0),
                    
                        full_page=av.get('fullpage', False),
                        ai_context_id=av.get('aiContextId', ''),
                        flags=av.get('flags', None),
                    
                        created_by=av.get('createdBy', ''),
                        created_date=av.get('createdDate', ''),
                        updated_by=av.get('updatedBy', ''),
                        updated_date=av.get('updatedDate', ''),
                        release_date=av.get('releasedDate', ''),
                        deleted_date=av.get('deletedDate', None),
                    )     
                
                self.versions.append(av_obj)
                
            # END for av in versions:
        # END if versions is not None and len(versions) > 0:
        
    # END def __init__():
    
    # 1. Equality check based on the unique ID
    def __eq__(self, other):
        if not isinstance(other, Asset):
            return NotImplemented
        return self.asset_id == other.asset_id
    # END def __eq__(self, other):
    
    # 2. Hash value based on the unique ID
    def __hash__(self):
        # We hash the unique, immutable ID (or a tuple of immutable unique fields)
        return hash(self.asset_id)
    # END def __hash__(self):
        
    
# END class Asset

@dataclass
class AssetVersion:
    """Represents a Domo App AssetVersion."""
    
    Asset: Asset

    # New mandatory field comes after all inherited mandatory fields.
    asset_version_id: str
    design_id: str
    version: str
    draft: bool
    trusted: bool
    public_assets_enabled: bool
    
    size_width: str
    size_height: str
    
    full_page: bool

    ai_context_id: str
    flags: any

    created_by: str
    created_date: str
    updated_by: str
    updated_date: str
    release_date: str
    deleted_date: str
    
    # Now fields with defaults
    scopes: List[any] = field(default_factory=list) # List of group IDs
    datasets_mapping: List[any] = field(default_factory=list) # List of group IDs
    collections_mapping: List[any] = field(default_factory=list) # List of group IDs
    accounts_mapping: List[any] = field(default_factory=list) # List of group IDs
    actions_mapping: List[any] = field(default_factory=list) # List of group IDs
    workflows_mapping: List[any] = field(default_factory=list) # List of group IDs
    packages_mapping: List[any] = field(default_factory=list) # List of group IDs
    
    def __init__(self, asset:Asset, asset_version_id, design_id, version, draft, trusted, public_assets_enabled, scopes, datasets_mapping, collections_mapping, accounts_mapping, actions_mapping, workflows_mapping, packages_mapping, size_width, size_height, full_page, ai_context_id, flags, created_by, created_date, updated_by, updated_date, release_date, deleted_date):
        
        self.Asset = asset
        
        self.asset_version_id = asset_version_id
        self.design_id = design_id
        self.version = version
        
        self.draft = draft
        
        self.trusted = trusted
        self.public_assets_enabled = public_assets_enabled
        self.scopes = scopes

        self.datasets_mapping = datasets_mapping
        self.collections_mapping = collections_mapping
        self.accounts_mapping = accounts_mapping
        self.actions_mapping = actions_mapping
        self.workflows_mapping = workflows_mapping
        self.packages_mapping = packages_mapping
        
        self.size_width = size_width
        self.size_height = size_height

        self.full_page = full_page
        self.ai_context_id = ai_context_id
        self.flags = flags

        self.created_by = created_by
        self.created_date = created_date
        self.updated_by = updated_by
        self.updated_date = updated_date
        self.release_date = release_date
        self.deleted_date = deleted_date
        
    # END def __init__():
        
# END class User
