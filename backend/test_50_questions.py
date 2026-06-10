#!/usr/bin/env python3
"""
Comprehensive 50-Question System Test
Tests the Industrial Agent AI with 50 real-world maintenance questions.
Equipment tag: 1PH718 (Motor Manual)
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/chat"
EQUIPMENT_TAG = "Process"  # The 1PH718 manual is tagged as "Process" in the database
OUTPUT_FILE = "test_results_50_questions.json"
RESULTS_DIR = Path("test_results")

# 50 Test Questions
QUESTIONS = [
    "What specific grade of danger indicates that minor personal injury can result if proper precautions are not taken?",
    "Who is authorized to commission, ground, and label devices, systems, and circuits under the qualified personnel guidelines?",
    "What are the five safety rules that must always be observed when working on the device to prevent material damage and personal injury?",
    "Why is it strictly forbidden for persons with heart pacemakers to enter areas where installations like transformers, converters, or motors are operating?",
    "According to the ESD guidelines, what household material can be used to wrap electronic modules if they must be stored in non-conducting packaging?",
    "Which EN standards do the three-phase asynchronous machine 1PH7 series conform to according to the EC Declaration of Conformity?",
    "What are the key performance and design characteristics that define the three-phase motors of the 1PH7 series for industrial drives?",
    "What is the weight specified on the sample rating plate for the 1PH7 186-2HF230EA9-Z motor model?",
    "What type of temperature sensor is permanently installed in the stator winding to monitor the three-phase motor?",
    "What is the minimum clearance distance required from customer-added devices at the air intake and outlet openings?",
    "Following up on the air intake question: What can happen to the motor if the cooling capacity is reduced due to missing cover sheets?",
    "Final follow-up on cooling: Which specific cooling method code and DIN EN IEC standard governs this enclosed cooling circuit design?",
    "What is the maximum permissible operating speed for flange-mounted construction types such as IM B5, IM V1, and IM V3?",
    "To which components should hoisting gear be attached when lifting or transporting the motors, and which auxiliary attachments must be avoided for lifting the full motor?",
    "What is the approximate weight of a standard IM B3 version of the 1PH7 184 motor type?",
    "What structural damage can occur inside the machine if condensation water collects and the stator winding becomes damp?",
    "By how much is the nominal degree of protection reduced if the plastic plugs or screw plugs are removed from the water drain holes?",
    "What temperature can the enclosure components of electric motors potentially exceed during continuous operational periods?",
    "What is the exact volumetric flow and internal pressure drop value specified for the 1PH7 18. motors with a pipe connection?",
    "What does the rotor balancing code 'H' indicate when found on the end face at the drive end of the shaft?",
    "What is the typical measuring surface sound pressure level $Lp(A)$ and its tolerance for the 1PH718 series within a speed range of 0 to 5000 rpm?",
    "When mounting the motor via its feet, what are the requirements for the strength class and thread size of the fixing bolts according to ISO 898-1?",
    "What phase sequence connection to terminals U, V, and W is required to achieve a standard clockwise direction of rotation?",
    "In the terminal box assignment table, what is the maximum current per terminal allowed for a 1PH7184 motor with a 1XB7 322 terminal box when applying a 0.6 reduction factor?",
    "What is the specified tightening torque value for the main M12 contact nuts and fixing bolts on the motor?",
    "Before closing the terminal box, what is the minimum required clearance in air that must be verified between live components?",
    "What is the prescribed tightening torque for the M8 fixing screws on a 1XB7 422 terminal box lid?",
    "What anti-corrosion agent is explicitly recommended for treating the clean contact surfaces of the ground conductor connection?",
    "What are the grounding terminal bolt tightening torques for terminal box types 1XB7 322 and 1XB7 422 respectively?",
    "Following up on the terminal box components: What protective circuit mechanism must be provided to prevent motor operation regarding the fan?",
    "Next follow-up: If a standard fan is operated on a 60 Hz system with ventilation from DE to NDE, what extra component must be screwed on?",
    "Final follow-up on the fan assembly: What danger exists if deposits accumulate on the fan impeller during long-term service?",
    "How far can the Sensor Module mounted on the terminal box be rotated to adjust cable outlet directions?",
    "What is the typical twisting moment range required to rotate the Sensor Module by hand without damaging the unit?",
    "What is the maximum number of times the rotation angle of the Sensor Module can be changed within its permissible range over its lifespan?",
    "At what specific temperature range must the insulation resistance of the winding to the motor enclosure always be measured?",
    "What is the minimum insulation resistance limit value at 25°C for new, cleaned, or repaired stator windings when the rated voltage is under 2 kV?",
    "What is the critical specific insulation resistance threshold for a motor winding after a long operating period?",
    "What immediate maintenance actions must be performed if the measured critical insulation resistance value is reached or found insufficient?",
    "After what storage or standstill period must the motor bearings be relubricated or have their grease completely replaced?",
    "What is the short-period permissible maximum operating speed limit ($n_{max}$) defined as the critical speed for these standard motors?",
    "What are the first signs or operational deviations that indicate a motor is no longer functioning correctly and requires technician intervention?",
    "Following up on operational deviations: What are the potential consequences if an operator removes or opens the safety covers while the motor is actively running?",
    "Next follow-up: If mechanical troubleshooting is required, what are the three listed mechanical fault characteristics in the diagnosis table?",
    "Final follow-up on the diagnosis table: If the motor experiences radial or axial vibration due to poor alignment, what specific remedial measures must be executed?",
    "Under normal operating conditions, after how many operating hours or months must the initial inspection of the three-phase motor be conducted?",
    "What is the general inspection interval required for a major service overhaul, and what is the maximum elapsed time allowed before performing it?",
    "What is the maximum permissible vibration severity level when checking the external fan on the end shield of the impeller-side motor bearing?",
    "Which rolling-contact bearing grease is explicitly stated as the product used for initial lubrication prior to plant delivery?",
    "What non-hardening joint sealant product is authorized to coat the bare joints between the enclosure and end shields to maintain the IP55 degree of protection?",
]


def test_question(question: str, question_num: int) -> dict:
    """
    Test a single question against the API.
    
    Returns:
        dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Question {question_num}/50")
    print(f"{'='*80}")
    print(f"Q: {question[:100]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            json={
                "query": question,
                "equipment_tag": EQUIPMENT_TAG,
                "session_id": f"test_session_{question_num}"
            },
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            answer = data.get("answer", "")
            citations = data.get("citations", [])
            
            # Extract key metrics
            result = {
                "question_num": question_num,
                "question": question,
                "status": "success",
                "response_time": round(elapsed_time, 2),
                "answer": answer,
                "answer_length": len(answer),
                "citations_count": len(citations),
                "citations": [
                    {
                        "ref": c.get("ref", ""),
                        "page": c.get("page_number", 0),
                        "section": c.get("section_heading", "")
                    }
                    for c in citations
                ],
                "has_citations": len(citations) > 0,
                "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer
            }
            
            # Print summary
            print(f"✓ SUCCESS ({elapsed_time:.2f}s)")
            print(f"  Citations: {len(citations)}")
            if citations:
                print(f"  Primary source: Page {citations[0].get('page_number', '?')}, {citations[0].get('section_heading', 'Unknown')[:50]}")
            print(f"  Answer preview: {answer[:150]}...")
            
            return result
            
        else:
            elapsed_time = time.time() - start_time
            print(f"✗ FAILED (HTTP {response.status_code})")
            return {
                "question_num": question_num,
                "question": question,
                "status": "http_error",
                "response_time": round(elapsed_time, 2),
                "error_code": response.status_code,
                "error_message": response.text[:200]
            }
            
    except requests.Timeout:
        elapsed_time = time.time() - start_time
        print(f"✗ TIMEOUT ({elapsed_time:.2f}s)")
        return {
            "question_num": question_num,
            "question": question,
            "status": "timeout",
            "response_time": round(elapsed_time, 2),
            "error_message": "Request timed out after 60 seconds"
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        return {
            "question_num": question_num,
            "question": question,
            "status": "exception",
            "response_time": round(elapsed_time, 2),
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


def generate_summary(results: list) -> dict:
    """Generate test summary statistics."""
    
    total = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total - successful
    
    success_rate = (successful / total * 100) if total > 0 else 0
    
    # Response time stats (only successful)
    response_times = [r["response_time"] for r in results if r["status"] == "success"]
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    min_time = min(response_times) if response_times else 0
    max_time = max(response_times) if response_times else 0
    
    # Citation stats
    citation_counts = [r["citations_count"] for r in results if r["status"] == "success"]
    avg_citations = sum(citation_counts) / len(citation_counts) if citation_counts else 0
    questions_with_citations = sum(1 for r in results if r.get("has_citations", False))
    
    # Answer length stats
    answer_lengths = [r["answer_length"] for r in results if r["status"] == "success"]
    avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
    
    return {
        "total_questions": total,
        "successful": successful,
        "failed": failed,
        "success_rate_percent": round(success_rate, 2),
        "response_time_stats": {
            "average_seconds": round(avg_time, 2),
            "min_seconds": round(min_time, 2),
            "max_seconds": round(max_time, 2)
        },
        "citation_stats": {
            "average_per_question": round(avg_citations, 2),
            "questions_with_citations": questions_with_citations,
            "citation_rate_percent": round((questions_with_citations / successful * 100) if successful > 0 else 0, 2)
        },
        "answer_stats": {
            "average_length_chars": round(avg_answer_length, 0)
        }
    }


def print_final_summary(summary: dict):
    """Print final test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\n📊 Overall Results:")
    print(f"   Total questions: {summary['total_questions']}")
    print(f"   Successful: {summary['successful']} ✓")
    print(f"   Failed: {summary['failed']} ✗")
    print(f"   Success rate: {summary['success_rate_percent']}%")
    
    print(f"\n⏱️  Response Time:")
    print(f"   Average: {summary['response_time_stats']['average_seconds']}s")
    print(f"   Min: {summary['response_time_stats']['min_seconds']}s")
    print(f"   Max: {summary['response_time_stats']['max_seconds']}s")
    
    print(f"\n📚 Citations:")
    print(f"   Average per answer: {summary['citation_stats']['average_per_question']}")
    print(f"   Questions with citations: {summary['citation_stats']['questions_with_citations']}/{summary['successful']}")
    print(f"   Citation rate: {summary['citation_stats']['citation_rate_percent']}%")
    
    print(f"\n📝 Answer Quality:")
    print(f"   Average answer length: {summary['answer_stats']['average_length_chars']} characters")
    
    print("\n" + "="*80)


def main():
    """Run the complete 50-question test."""
    
    print("="*80)
    print("INDUSTRIAL AGENT AI - 50 QUESTION COMPREHENSIVE TEST")
    print("="*80)
    print(f"Equipment tag: {EQUIPMENT_TAG}")
    print(f"API endpoint: {API_URL}")
    print(f"Total questions: {len(QUESTIONS)}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check if server is running
    try:
        requests.get("http://localhost:8000/documents", timeout=5)
        print("✓ Server is running")
    except:
        print("✗ ERROR: Backend server is not running!")
        print("  Please start the server: cd backend && uvicorn main:app --reload")
        return
    
    # Create results directory
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Run tests
    results = []
    start_time = time.time()
    
    for i, question in enumerate(QUESTIONS, 1):
        result = test_question(question, i)
        results.append(result)
        
        # Small delay between requests
        time.sleep(0.5)
    
    total_time = time.time() - start_time
    
    # Generate summary
    summary = generate_summary(results)
    summary["total_test_time_seconds"] = round(total_time, 2)
    summary["test_timestamp"] = datetime.now().isoformat()
    
    # Save results
    output_data = {
        "summary": summary,
        "results": results
    }
    
    output_path = RESULTS_DIR / OUTPUT_FILE
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")
    
    # Print final summary
    print_final_summary(summary)
    
    print(f"\n⏱️  Total test time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    print(f"📁 Full results: {output_path}")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
