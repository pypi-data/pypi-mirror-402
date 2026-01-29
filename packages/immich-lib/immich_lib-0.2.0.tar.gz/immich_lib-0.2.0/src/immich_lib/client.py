from .base import ImmichBaseClient
from .api.activities import ActivitiesMixin
from .api.albums import AlbumsMixin
from .api.assets import AssetsMixin
from .api.users import UsersMixin
from .api.system import SystemMixin
from .api.search import SearchMixin
from .api.trash import TrashMixin
from .api.people import PeopleMixin
from .api.partners import PartnersMixin
from .api.tags import TagsMixin
from .api.stacks import StacksMixin
from .api.folders import FoldersMixin
from .api.jobs import JobsMixin
from .api.misc import MiscellaneousMixin

class ImmichClient(
    ActivitiesMixin,
    AlbumsMixin,
    AssetsMixin,
    UsersMixin,
    SystemMixin,
    SearchMixin,
    TrashMixin,
    PeopleMixin,
    PartnersMixin,
    TagsMixin,
    StacksMixin,
    FoldersMixin,
    JobsMixin,
    MiscellaneousMixin
):
    """
    Unified client for Immich API, combining all category mixins.
    """
    def __init__(self, server_url, api_key):
        super().__init__(server_url, api_key)
