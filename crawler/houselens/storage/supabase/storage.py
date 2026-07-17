from ..interfaces import IStorage
from .client import SupabaseClientManager

from .mixins.property import SupabasePropertyMixin
from .mixins.community import SupabaseCommunityMixin
from .mixins.queue import SupabaseQueueMixin

class SupabaseStorage(SupabasePropertyMixin, SupabaseCommunityMixin, SupabaseQueueMixin, IStorage):
    """
    Storage implementation that saves data directly to Supabase PostgREST API.
    Composed of Mixins for separation of concerns.
    """
    def __init__(self):
        self.client = SupabaseClientManager.get_client()
