import logging
from typing import Any

class SupabaseCommunityMixin:
    """
    Mixin for Community and Builder related Supabase storage operations.
    Requires `self.client` to be defined in the main class.
    """
    def save_community(self, community_data: Any) -> bool:
        try:
            from ....models.community import StandardCommunity
            if isinstance(community_data, StandardCommunity):
                community_dict = community_data.model_dump(exclude_none=True)
            else:
                community_dict = community_data
            
            builder_name = community_dict.pop('builder', None)
            if builder_name:
                community_dict['builder_name_raw'] = builder_name
            builder_id = None
            
            if builder_name:
                b_res = self.client.table("builder").select("builder_id").eq("name", builder_name).execute()
                
                if b_res.data and len(b_res.data) > 0:
                    builder_id = b_res.data[0]['builder_id']
                else:
                    insert_res = self.client.table("builder").insert({"name": builder_name}).execute()
                    if insert_res.data:
                        builder_id = insert_res.data[0]['builder_id']
                        logging.info(f"[SupabaseStorage] Auto-created new builder: {builder_name}")
            
            if builder_id:
                community_dict['builder_id'] = builder_id
                
            response = self.client.table("community").upsert(community_dict).execute()
            
            if response.data:
                logging.info(f"[SupabaseStorage] Successfully saved community {community_dict.get('community_uuid')}")
                return True
            else:
                return False
                
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error saving community: {e}")
            return False
