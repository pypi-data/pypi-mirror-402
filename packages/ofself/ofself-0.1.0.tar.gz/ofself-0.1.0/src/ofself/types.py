"""
OfSelf SDK Type Definitions

Pydantic models for API request and response types.
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Node Types
# ============================================================================

class Node(BaseModel):
    """Represents a node in the user's graph."""
    
    id: str
    title: str
    value: Optional[str] = None
    node_type: str = Field(default="note", alias="type")
    owner_id: str
    created_at: datetime
    updated_at: datetime
    node_metadata: Optional[dict[str, Any]] = None
    tag_ids: list[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class NodeCreate(BaseModel):
    """Data for creating a new node."""
    
    title: str
    value: Optional[str] = None
    node_type: str = Field(default="note", alias="type")
    node_metadata: Optional[dict[str, Any]] = None
    tag_ids: Optional[list[str]] = None
    
    class Config:
        populate_by_name = True


class NodeUpdate(BaseModel):
    """Data for updating a node."""
    
    title: Optional[str] = None
    value: Optional[str] = None
    node_type: Optional[str] = Field(default=None, alias="type")
    node_metadata: Optional[dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


# ============================================================================
# Tag Types
# ============================================================================

class Tag(BaseModel):
    """Represents a tag."""
    
    id: str
    name: str
    color: Optional[str] = None
    owner_id: str
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    """Data for creating a new tag."""
    
    name: str
    color: Optional[str] = None


class TagUpdate(BaseModel):
    """Data for updating a tag."""
    
    name: Optional[str] = None
    color: Optional[str] = None


# ============================================================================
# File Types
# ============================================================================

class File(BaseModel):
    """Represents an uploaded file."""
    
    id: str
    filename: str
    content_type: str
    size: int
    owner_id: str
    created_at: datetime
    updated_at: datetime
    tag_ids: list[str] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None


class FileUpdate(BaseModel):
    """Data for updating file metadata."""
    
    filename: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


# ============================================================================
# Relationship Types
# ============================================================================

class Relationship(BaseModel):
    """Represents a relationship between two nodes."""
    
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    weight: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class RelationshipCreate(BaseModel):
    """Data for creating a relationship."""
    
    source_node_id: str
    target_node_id: str
    relationship_type: str
    weight: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class RelationshipUpdate(BaseModel):
    """Data for updating a relationship."""
    
    relationship_type: Optional[str] = None
    weight: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


# ============================================================================
# Exposure Profile Types
# ============================================================================

class ExposureProfile(BaseModel):
    """Represents an exposure profile (what data is shared)."""
    
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    scope: dict[str, Any]  # Defines what's exposed
    created_at: datetime
    updated_at: datetime
    is_default: bool = False


class ExposureProfileCreate(BaseModel):
    """Data for creating an exposure profile."""
    
    name: str
    description: Optional[str] = None
    scope: dict[str, Any]


class ExposureProfileUpdate(BaseModel):
    """Data for updating an exposure profile."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[dict[str, Any]] = None
    is_default: Optional[bool] = None


# ============================================================================
# Sharing Types
# ============================================================================

class Share(BaseModel):
    """Represents a data share between users or apps."""
    
    id: str
    owner_id: str
    recipient_id: Optional[str] = None
    third_party_id: Optional[str] = None
    exposure_profile_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ShareCreate(BaseModel):
    """Data for creating a share."""
    
    recipient_id: Optional[str] = None
    third_party_id: Optional[str] = None
    exposure_profile_id: str
    expires_at: Optional[datetime] = None


# ============================================================================
# Proposal Types
# ============================================================================

class Proposal(BaseModel):
    """Represents a proposal for data changes."""
    
    id: str
    owner_id: str
    third_party_id: str
    proposal_type: str  # create_node, update_node, merge_nodes, etc.
    status: str  # pending, approved, rejected
    canonical_data: dict[str, Any]
    raw_data: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None


class ProposalCreate(BaseModel):
    """Data for creating a proposal."""
    
    proposal_type: str
    canonical_data: dict[str, Any]
    raw_data: Optional[dict[str, Any]] = None


# ============================================================================
# Pagination Types
# ============================================================================

class PaginatedResponse(BaseModel):
    """Paginated API response."""
    
    items: list[Any]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    
    page: int = 1
    per_page: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "desc"  # asc or desc


