"""
Check Qdrant collection status, indexes, and document counts.
"""

import logging
from vectorstore.qdrant_store import get_client, list_documents
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_collection_status():
    """Check collection info, indexes, and document counts."""
    client = get_client()
    
    print("\n" + "="*60)
    print("QDRANT COLLECTION STATUS")
    print("="*60)
    
    try:
        # Get collection info
        collection_info = client.get_collection(config.QDRANT_COLLECTION)
        print(f"\n📊 Collection: {config.QDRANT_COLLECTION}")
        print(f"   Points count: {collection_info.points_count}")
        print(f"   Vectors: {list(collection_info.config.params.vectors.keys())}")
        
        # Check indexes
        print(f"\n🔍 Payload Indexes:")
        if collection_info.payload_schema:
            for field_name, field_info in collection_info.payload_schema.items():
                print(f"   - {field_name}: {field_info.data_type}")
        else:
            print("   No payload indexes found")
        
        # Get parent collection info
        parent_collection = f"{config.QDRANT_COLLECTION}_parents"
        try:
            parent_info = client.get_collection(parent_collection)
            print(f"\n📊 Parent Collection: {parent_collection}")
            print(f"   Points count: {parent_info.points_count}")
            
            print(f"\n🔍 Parent Payload Indexes:")
            if parent_info.payload_schema:
                for field_name, field_info in parent_info.payload_schema.items():
                    print(f"   - {field_name}: {field_info.data_type}")
            else:
                print("   No payload indexes found")
        except Exception as e:
            print(f"\n⚠️  Parent collection error: {e}")
        
        # List documents
        print(f"\n📄 Uploaded Documents:")
        docs = list_documents()
        if docs:
            for doc in docs:
                print(f"   - {doc['doc_name']}")
                print(f"     Equipment Tag: {doc['equipment_tag']}")
                print(f"     Doc ID: {doc['doc_id']}")
                print(f"     Chunks: {doc['chunk_count']}")
                print()
        else:
            print("   No documents found")
        
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error checking collection: {e}\n")


if __name__ == "__main__":
    check_collection_status()
