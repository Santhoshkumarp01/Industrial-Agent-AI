"""
Delete all documents with specific equipment tags from Qdrant.
Used to remove duplicates or incorrectly tagged documents.
"""

import logging
from vectorstore.qdrant_store import get_client
from config import config
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_by_equipment_tags(tags_to_delete: list[str]):
    """Delete all chunks with specified equipment tags."""
    client = get_client()
    
    for tag in tags_to_delete:
        try:
            # Delete from main collection
            result = client.delete(
                collection_name=config.QDRANT_COLLECTION,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="equipment_tag",
                                match=MatchValue(value=tag)
                            )
                        ]
                    )
                ),
            )
            logger.info(f"✅ Deleted chunks with equipment_tag='{tag}' from main collection")
            print(f"✅ Deleted chunks with equipment_tag='{tag}' from main collection")
            
            # Delete from parent collection
            try:
                parent_collection = f"{config.QDRANT_COLLECTION}_parents"
                result = client.delete(
                    collection_name=parent_collection,
                    points_selector=FilterSelector(
                        filter=Filter(
                            must=[
                                FieldCondition(
                                    key="equipment_tag",
                                    match=MatchValue(value=tag)
                                )
                            ]
                        )
                    ),
                )
                logger.info(f"✅ Deleted parent sections with equipment_tag='{tag}'")
                print(f"✅ Deleted parent sections with equipment_tag='{tag}'")
            except Exception as e:
                logger.warning(f"⚠️  Could not delete from parent collection: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error deleting equipment_tag='{tag}': {e}")
            print(f"❌ Error deleting equipment_tag='{tag}': {e}")


if __name__ == "__main__":
    # Tags to delete (duplicates with typos)
    tags_to_delete = [
        "ac-driver-motor",           # Typo: should be "ac-drive-motor"
        "general-industrial-mootor"  # Typo: should be "general-industrial-motor"
    ]
    
    print("⚠️  WARNING: This will delete all documents with these equipment tags:")
    for tag in tags_to_delete:
        print(f"   - {tag}")
    
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        delete_by_equipment_tags(tags_to_delete)
        print("\n✅ Duplicate equipment tags removed!")
    else:
        print("❌ Operation cancelled.")
