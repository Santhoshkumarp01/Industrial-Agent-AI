"""
Test script to check what's actually in Qdrant for equipment manuals
"""
import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "maintenance_docs"  # From config.py

def test_qdrant_content():
    """Check what equipment tags are stored in Qdrant"""
    
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    print("=" * 80)
    print("TESTING QDRANT CONTENT")
    print("=" * 80)
    
    # Check collection exists
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"\n✅ Collection '{COLLECTION_NAME}' exists")
        print(f"   Points count: {collection_info.points_count}")
        print(f"   Vectors config: {collection_info.config.params.vectors}")
    except Exception as e:
        print(f"\n❌ Collection error: {e}")
        return
    
    # Get sample points to see what equipment_tags are stored
    print("\n" + "=" * 80)
    print("CHECKING EQUIPMENT TAGS IN QDRANT")
    print("=" * 80)
    
    try:
        # Scroll through points to get unique equipment_tags
        equipment_tags = set()
        doc_names = set()
        
        offset = None
        limit = 100
        total_checked = 0
        
        while True:
            result = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            for point in points:
                payload = point.payload or {}
                eq_tag = payload.get("equipment_tag", "")
                doc_name = payload.get("doc_name", "")
                
                if eq_tag:
                    equipment_tags.add(eq_tag)
                if doc_name:
                    doc_names.add(doc_name)
            
            total_checked += len(points)
            
            if next_offset is None:
                break
            offset = next_offset
        
        print(f"\n✅ Checked {total_checked} points")
        
        print(f"\n📋 Unique equipment_tags found ({len(equipment_tags)}):")
        for tag in sorted(equipment_tags):
            print(f"   - '{tag}'")
        
        print(f"\n📄 Unique doc_names found ({len(doc_names)}):")
        for name in sorted(doc_names):
            print(f"   - '{name}'")
        
    except Exception as e:
        print(f"\n❌ Error scrolling collection: {e}")
        return
    
    # Test retrieval for each machine
    print("\n" + "=" * 80)
    print("TESTING RETRIEVAL FOR EACH MACHINE")
    print("=" * 80)
    
    from sensors.machine_logs import MACHINE_TAG_TO_EQUIPMENT_TAG
    
    for machine_tag, equipment_tag in MACHINE_TAG_TO_EQUIPMENT_TAG.items():
        print(f"\n🔍 Machine: {machine_tag}")
        print(f"   Equipment tag: '{equipment_tag}'")
        
        # Check if this equipment_tag exists in Qdrant
        if equipment_tag in equipment_tags:
            print(f"   ✅ Found in Qdrant")
            
            # Try a test search
            try:
                from retrieval.retriever import retrieve
                
                test_query = f"What are the maintenance procedures for {equipment_tag}?"
                chunks, metadata = retrieve(
                    query=test_query,
                    equipment_tag=equipment_tag,
                    use_query_rewriting=False,
                    use_parent_retrieval=False,
                )
                
                print(f"   📊 Retrieved {len(chunks)} chunks")
                if chunks:
                    print(f"   📖 First chunk: {chunks[0].section_heading[:60]}...")
                else:
                    print(f"   ⚠️  No chunks retrieved for test query")
                    
            except Exception as e:
                print(f"   ❌ Retrieval failed: {e}")
        else:
            print(f"   ❌ NOT FOUND in Qdrant")
            print(f"   💡 Check if PDF was uploaded with correct equipment_tag")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_qdrant_content()
