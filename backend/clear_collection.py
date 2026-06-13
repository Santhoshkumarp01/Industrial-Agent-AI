"""
Clear all data from Qdrant collection (both main and parent collections).
Run this when you want to start fresh with new equipment tags.
"""

import logging
from vectorstore.qdrant_store import get_client
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_collection():
    """Delete and recreate the Qdrant collection."""
    client = get_client()
    
    collections_to_clear = [
        config.QDRANT_COLLECTION,
        f"{config.QDRANT_COLLECTION}_parents"
    ]
    
    for collection_name in collections_to_clear:
        try:
            # Check if collection exists
            existing = [c.name for c in client.get_collections().collections]
            
            if collection_name in existing:
                client.delete_collection(collection_name)
                logger.info(f"✅ Deleted collection: {collection_name}")
                print(f"✅ Deleted collection: {collection_name}")
            else:
                logger.info(f"ℹ️  Collection does not exist: {collection_name}")
                print(f"ℹ️  Collection does not exist: {collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error deleting {collection_name}: {e}")
            print(f"❌ Error deleting {collection_name}: {e}")
    
    print("\n✅ Collection cleared! You can now upload PDFs with correct equipment tags.")
    print("   The collection will be auto-created on first upload.")


if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL documents and equipment tags from Qdrant!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_collection()
    else:
        print("❌ Operation cancelled.")
