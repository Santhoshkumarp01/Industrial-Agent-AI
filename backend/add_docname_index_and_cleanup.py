"""
Add doc_name index and remove historical incidents by scrolling.
"""

import logging
from vectorstore.qdrant_store import get_client
from config import config
from qdrant_client.models import PayloadSchemaType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_docname_index():
    """Add doc_name index to main collection."""
    client = get_client()
    
    try:
        print("🔧 Adding doc_name index to main collection...")
        client.create_payload_index(
            collection_name=config.QDRANT_COLLECTION,
            field_name="doc_name",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("✅ doc_name index added")
        return True
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✅ doc_name index already exists")
            return True
        else:
            print(f"❌ Error: {e}")
            return False


def remove_historical_incidents_by_scroll():
    """Remove historical incidents by scrolling and filtering in code."""
    client = get_client()
    
    print("\n🧹 Removing historical incidents...")
    
    # Scroll all points
    results, _ = client.scroll(
        collection_name=config.QDRANT_COLLECTION,
        limit=3000,  # All chunks
        with_payload=["doc_name", "equipment_tag"],
        with_vectors=False,
    )
    
    # Find IDs to delete (historical incidents)
    ids_to_delete = []
    for point in results:
        doc_name = point.payload.get("doc_name", "")
        if "Historical Incidents" in doc_name:
            ids_to_delete.append(point.id)
    
    # Delete by IDs
    if ids_to_delete:
        client.delete(
            collection_name=config.QDRANT_COLLECTION,
            points_selector=ids_to_delete,
        )
        print(f"✅ Deleted {len(ids_to_delete)} historical incident chunks")
    else:
        print("ℹ️  No historical incidents found")


def verify():
    """Verify cleanup."""
    from vectorstore.qdrant_store import list_documents
    
    print("\n📋 Final Document List:")
    docs = list_documents()
    
    pdf_docs = [d for d in docs if d['doc_name'].endswith('.pdf')]
    
    print(f"\n✅ PDF Documents: {len(pdf_docs)}")
    for doc in pdf_docs:
        print(f"   - {doc['doc_name']}")
        print(f"     Equipment Tag: {doc['equipment_tag']}")
        print(f"     Chunks: {doc['chunk_count']}")
    
    if len(pdf_docs) == 4:
        print("\n✅ SUCCESS! Only the 4 main PDF documents remain")
    else:
        print(f"\n⚠️  Expected 4 PDFs, found {len(pdf_docs)}")


if __name__ == "__main__":
    print("="*60)
    print("ADDING INDEX AND CLEANUP")
    print("="*60 + "\n")
    
    add_docname_index()
    remove_historical_incidents_by_scroll()
    verify()
    
    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60 + "\n")
