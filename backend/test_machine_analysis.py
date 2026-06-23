"""
Test actual machine analysis to see if citations are generated
"""
import asyncio
import sys
from sensors.machine_logs import generate_log_entry, get_latest_logs
from api.machine_analysis_routes import analyze_machine
from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    include_logs: int = 10
    inject_anomaly: bool = True

async def test_analysis():
    """Run a test machine analysis"""
    
    machine_tag = "general-industrial-motor"
    
    print("=" * 80)
    print(f"TESTING MACHINE ANALYSIS FOR: {machine_tag}")
    print("=" * 80)
    
    # Inject an anomaly first
    print("\n1️⃣ Injecting anomaly...")
    entry = generate_log_entry(machine_tag, inject_anomaly=True)
    print(f"   ✅ Anomaly injected: {entry['severity']}")
    print(f"   Fault code: {entry['fault_code']}")
    print(f"   Event: {entry['event_summary']}")
    
    # Run analysis
    print("\n2️⃣ Running analysis...")
    request = AnalyzeRequest(include_logs=10, inject_anomaly=False)
    result = await analyze_machine(machine_tag, request)
    
    # Check results
    print("\n3️⃣ Analysis Results:")
    print(f"   Machine: {result['display_name']}")
    print(f"   Severity: {result['current_severity']}")
    print(f"   Fault code: {result['fault_code']}")
    print(f"   Mapped doc: {result['mapped_document']}")
    
    analysis = result['analysis']
    print(f"\n4️⃣ RAG Results:")
    print(f"   Answer length: {len(analysis['answer'])} chars")
    print(f"   Citations count: {len(analysis['citations'])}")
    print(f"   Grounded in doc: {analysis['grounded_in_doc']}")
    print(f"   Confidence: {analysis['confidence_level']}")
    
    if analysis['citations']:
        print(f"\n📚 Citations:")
        for cit in analysis['citations']:
            print(f"   [{cit['ref']}] Page {cit['page']}: {cit['section'][:60]}...")
    else:
        print(f"\n⚠️  NO CITATIONS GENERATED")
    
    print(f"\n📖 Answer preview:")
    print(f"   {analysis['answer'][:300]}...")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_analysis())
