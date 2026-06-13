"""
Delete parent sections by scrolling and filtering in code (no index required).
"""

import logging
from vectorstore.qdrant_store import get_client
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_parents_by_equipment_tags(tags_to_delete: list[str]):
    """Delete parent sections with specified equipment tags by scrolling."""
    client = get_client()
    parent_collection = f"{config.QDRANT_COLLECTION}_parents"
    
    try:
        # Scroll all parent sections
        results, _ = client.scroll(
            collection_name=parent_collection,
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )
        
        # Find IDs to delete
        ids_to_delete = []
        for point in results:
            equipment_tag = point.payload.get("equipment_tag", "")
            if equipment_tag in tags_to_delete:
                ids_to_delete.append(point.id)
                logger.info(f"Found parent to delete: {point.id} (equipment_tag={equipment_tag})")
        
        # Delete by IDs
        if ids_to_delete:
            client.delete(
                collection_name=parent_collection,
                points_selector=ids_to_delete,
            )
            logger.info(f"✅ Deleted {len(ids_to_delete)} parent sections")
            print(f"✅ Deleted {len(ids_to_delete)} parent sections with duplicate equipment tags")
        else:
            print("ℹ️  No parent sections found with those equipment tags")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    tags_to_delete = [
        "ac-driver-motor",
        "general-industrial-mootor"
    ]
    
    print("Deleting parent sections with duplicate equipment tags...")
    delete_parents_by_equipment_tags(tags_to_delete)
