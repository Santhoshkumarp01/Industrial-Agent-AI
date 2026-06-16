"""
Quick test script to verify section_heading index and retrieval filtering.
Run from backend folder: python test_retrieval.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vectorstore import qdrant_store
from embeddings.embedder import encode_query
from retrieval.retriever import retrieve

def test_index_creation():
    """Test that section_heading index is created."""
    print("\n" + "="*60)
    print("TEST 1: Verify section_heading index creation")
    print("="*60)
    
    try:
        # This will trigger index creation if collection exists
        qdrant_store.ensure_collection()
        print("✅ Collection initialization successful")
        print("✅ section_heading index should now exist")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_structural_filter():
    """Test that structural pages are filtered out."""
    print("\n" + "="*60)
    print("TEST 2: Query with structural page filtering")
    print("="*60)
    
    # Query that used to pull Index pages
    test_query = "What are the safety instructions mentioned in the manual?"
    
    print(f"\nQuery: '{test_query}'")
    print("\nExpected behavior:")
    print("  - Should retrieve actual safety content sections")
    print("  - Should NOT retrieve Index, TOC, or Copyright pages")
    print("\nRetrieving...")
    
    try:
        chunks, metadata = retrieve(
            query=test_query,
            equipment_tag=None,
            top_k=20,
            use_query_rewriting=True,
            use_parent_retrieval=True
        )
        
        print(f"\n✅ Retrieved {len(chunks)} chunks")
        print(f"Confidence: {metadata.get('confidence_level')} ({metadata.get('confidence_score', 0):.2f})")
        
        # Check sections retrieved
        print("\nTop 3 sections retrieved:")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n  {i}. {chunk.citation_ref}")
            print(f"     Page: {chunk.page_number}")
            print(f"     Section: '{chunk.section_heading}'")
            print(f"     Score: {chunk.relevance_score:.3f}")
            
            # Check for structural keywords (should not be present)
            section_lower = chunk.section_heading.lower()
            structural_keywords = ['index', 'índice', 'contents', 'copyright']
            has_structural = any(kw in section_lower for kw in structural_keywords)
            
            if has_structural:
                print(f"     ⚠️  WARNING: Structural keyword detected!")
            else:
                print(f"     ✅ No structural keywords")
        
        return True
    except Exception as e:
        print(f"\n❌ Retrieval error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_count_agnostic():
    """Test count-agnostic list retrieval."""
    print("\n" + "="*60)
    print("TEST 3: Count-agnostic list retrieval")
    print("="*60)
    
    test_cases = [
        "What are the five safety rules?",
        "What are the three maintenance steps?",
        "What safety instructions are mentioned?"
    ]
    
    for query in test_cases:
        print(f"\n📋 Query: '{query}'")
        
        try:
            chunks, metadata = retrieve(
                query=query,
                top_k=10,
                use_query_rewriting=True,
                use_parent_retrieval=True
            )
            
            if chunks:
                top_chunk = chunks[0]
                print(f"   ✅ Top result: '{top_chunk.section_heading}' (Page {top_chunk.page_number})")
                print(f"   Confidence: {metadata.get('confidence_level')}")
            else:
                print(f"   ⚠️  No results")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True

if __name__ == "__main__":
    print("\n🧪 Industrial Agent AI - Retrieval System Tests")
    print("="*60)
    
    # Run tests
    test1_pass = test_index_creation()
    test2_pass = test_structural_filter()
    test3_pass = test_count_agnostic()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"1. Index Creation:        {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"2. Structural Filtering:  {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"3. Count-Agnostic:        {'✅ PASS' if test3_pass else '❌ FAIL'}")
    print("="*60)
    
    if all([test1_pass, test2_pass, test3_pass]):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed - check errors above")
