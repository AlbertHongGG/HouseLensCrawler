import logging
from supabase import create_client, Client
from ...config import AppConfig

class SupabaseClientManager:
    """
    Singleton manager for the Supabase client.
    """
    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = AppConfig.SUPABASE_URL
            key = AppConfig.SUPABASE_SERVICE_ROLE_KEY
            
            # Since the URL in .env is a Postgres connection string, we need to extract the base URL
            # if the user put the postgres URL in SUPABASE_URL.
            # But wait, supabase-py expects a REST API URL like "http://localhost:8000".
            # The user put: postgresql://... in SUPABASE_URL.
            # We must parse it or ask the user to fix it!
            # Let's handle both cases.
            if url.startswith("postgresql://") or url.startswith("postgres://"):
                # Extract the host and port
                import re
                match = re.search(r"@([^:]+)", url)
                host = match.group(1) if match else "localhost"
                url = f"http://{host}:8000" # Assuming default API port is 8000 for local docker
                logging.info(f"[SupabaseClient] Parsed Postgres URL. Using REST API URL: {url}")
                
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
                
            from supabase import ClientOptions
            
            # Create client with schema set to houselens
            cls._instance = create_client(
                url, 
                key,
                options=ClientOptions(schema='houselens')
            )
            logging.info("[SupabaseClient] Initialized Supabase REST client.")
        return cls._instance
