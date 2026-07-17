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
                
            builder_ids = []
            
            if builder_name:
                import re
                names = [n.strip() for n in re.split(r'[、,，/ ]+', builder_name) if n.strip()]
                
                for name in names:
                    b_res = self.client.table("builder").select("builder_id").eq("name", name).execute()
                    
                    if b_res.data and len(b_res.data) > 0:
                        builder_ids.append(b_res.data[0]['builder_id'])
                    else:
                        insert_res = self.client.table("builder").insert({"name": name}).execute()
                        if insert_res.data:
                            builder_ids.append(insert_res.data[0]['builder_id'])
                            logging.info(f"[SupabaseStorage] Auto-created new builder: {name}")
            
            # Ensure community_uuid is assigned or extracted
            community_uuid = community_dict.get('community_uuid')
            
            response = self.client.table("community").upsert(community_dict).execute()
            
            if response.data:
                logging.info(f"[SupabaseStorage] Successfully saved community {community_uuid}")
                
                # Insert into many-to-many table
                if builder_ids and community_uuid:
                    for b_id in builder_ids:
                        try:
                            self.client.table("community_builders").insert({
                                "community_uuid": community_uuid,
                                "builder_id": b_id
                            }).execute()
                        except Exception as e:
                            if "duplicate key value" not in str(e):
                                logging.warning(f"[SupabaseStorage] Error linking builder {b_id} to community {community_uuid}: {e}")
                                
                return True
            else:
                return False
                
        except Exception as e:
            logging.error(f"[SupabaseStorage] Error saving community: {e}", exc_info=True)
            return False
