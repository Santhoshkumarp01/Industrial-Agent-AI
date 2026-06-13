"""
1. Add equipment_tag index to parent collection
2. Remove historical incidents with wrong equipment tags
"""

import logging
from vectorstore.qdrant_store import get_client
from config import config
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector, PayloadSchemaType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_parent_collection_index():
    """Add equipment_tag index to parent collection."""
    client = get_client()
    parent_collection = f"{config.QDRANT_COLLECTION}_parents"
    
    try:
        print("\n🔧 Adding equipment_tag index to parent collection...")
        client.create_payload_index(
            collection_name=parent_collection,
            field_name="equipment_tag",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("✅ equipment_tag index added to parent collection")
        logger.info("Added equipment_tag index to parent collection")
        return True
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✅ equipment_tag index already exists")
            return True
        else:
            print(f"❌ Error adding index: {e}")
            logger.error(f"Error adding index: {e}")
            return False


def cleanup_historical_incidents():
    """Remove historical incidents with wrong equipment tags."""
    client = get_client()
    
    print("\n🧹 Cleaning up historical incidents with incorrect tags...")
    
    # Tags to remove (these are from the old indexing with kebab-case)
    tags_to_remove = [
        "ac-drive-motor",
        "general-industrial-motor",
        "heavy-duty-industrial-motor",
        "synchronous-motor"
    ]
    
    total_deleted = 0
    
    for tag in tags_to_remove:
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
                            ),
                            FieldCondition(
                                key="doc_name",
                                match=MatchValue(value="Steel Plant Historical Incidents")
                            )
                        ]
                    )
                ),
            )
            print(f"   ✅ Removed historical incidents with tag: {tag}")
            total_deleted += 1
            
        except Exception as e:
            print(f"   ⚠️  Could not remove tag '{tag}': {e}")
    
    print(f"✅ Cleaned up {total_deleted} historical incident tags")
    print("\n💡 Historical incidents will be re-indexed on next app restart with correct tags")


def verify_cleanup():
    """Verify the cleanup was successful."""
    from vectorstore.qdrant_store import list_documents
    
    print("\n📋 Final Document List:")
    docs = list_documents()
    
    pdf_docs = [d for d in docs if d['doc_name'].endswith('.pdf')]
    incident_docs = [d for d in docs if 'Historical' in d['doc_name']]
    
    print(f"\n✅ PDF Documents: {len(pdf_docs)}")
    for doc in pdf_docs:
        print(f"   - {doc['doc_name']}")
        print(f"     Equipment Tag: {doc['equipment_tag']}")
        print(f"     Chunks: {doc['chunk_count']}")
    
    print(f"\n⚠️  Historical Incidents: {len(incident_docs)}")
    for doc in incident_docs:
        print(f"   - Equipment Tag: {doc['equipment_tag']} (Chunks: {doc['chunk_count']})")
    
    if len(pdf_docs) == 4 and len(incident_docs) == 0:
        print("\n✅ SUCCESS! Only the 4 PDF documents remain")
    else:
        print(f"\n⚠️  Expected 4 PDFs and 0 incidents, found {len(pdf_docs)} PDFs and {len(incident_docs)} incidents")


if __name__ == "__main__":
    print("="*60)
    print("FIXING QDRANT INDEXING AND CLEANUP")
    print("="*60)
    
    # Step 1: Add index to parent collection
    fix_parent_collection_index()
    
    # Step 2: Remove historical incidents with wrong tags
    cleanup_historical_incidents()
    
    # Step 3: Verify
    verify_cleanup()
    
    print("\n" + "="*60)
    print("✅ ALL DONE!")
    print("="*60 + "\n")
