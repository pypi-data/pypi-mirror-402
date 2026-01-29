"""
OfSelf API Resources

Each resource maps to a namespace on the client:
    - client.auth          # User authentication
    - client.users         # User profiles & API keys
    - client.nodes         # Notes, documents, entities
    - client.tags          # Organize with tags
    - client.files         # File uploads
    - client.relationships # Node connections
    - client.embeddings    # Vector embeddings
    - client.graph         # Graph visualization
    - client.exposure_profiles  # Data access control
    - client.sharing       # Share with users/apps
    - client.authorizations # Manage app access
    - client.proposals     # Data change proposals
    - client.audit         # Audit logs
    - client.webhooks      # Real-time events
"""

from ofself.resources.auth import AuthResource
from ofself.resources.users import UsersResource
from ofself.resources.nodes import NodesResource
from ofself.resources.tags import TagsResource
from ofself.resources.files import FilesResource
from ofself.resources.relationships import RelationshipsResource
from ofself.resources.embeddings import EmbeddingsResource
from ofself.resources.graph import GraphResource
from ofself.resources.exposure_profiles import ExposureProfilesResource
from ofself.resources.sharing import SharingResource
from ofself.resources.authorizations import AuthorizationsResource
from ofself.resources.proposals import ProposalsResource
from ofself.resources.audit import AuditResource
from ofself.resources.webhooks import WebhooksResource
from ofself.resources.follows import FollowsResource
from ofself.resources.history import HistoryResource
from ofself.resources.third_party import ThirdPartyResource

__all__ = [
    "AuthResource",
    "UsersResource",
    "NodesResource",
    "TagsResource",
    "FilesResource",
    "RelationshipsResource",
    "EmbeddingsResource",
    "GraphResource",
    "ExposureProfilesResource",
    "SharingResource",
    "AuthorizationsResource",
    "ProposalsResource",
    "AuditResource",
    "WebhooksResource",
    "FollowsResource",
    "HistoryResource",
    "ThirdPartyResource",
]

