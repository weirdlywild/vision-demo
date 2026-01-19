#!/usr/bin/env python3
"""
Quick test script for DIY Repair Diagnosis API.
Usage: python test_api.py <image_path>
"""

import sys
import requests


def test_diagnose(image_path: str, base_url: str = "http://localhost:8000"):
    """Test the /diagnose endpoint."""
    print(f"Testing API at {base_url}")
    print(f"Uploading image: {image_path}")
    print("-" * 60)

    # Open and upload image
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(f"{base_url}/diagnose", files=files)

    print(f"Status Code: {response.status_code}")
    print()

    if response.status_code == 200:
        data = response.json()

        print("DIAGNOSIS:")
        print(f"  Issue: {data.get('diagnosis')}")
        print(f"  Confidence: {data.get('confidence', 0):.2%}")
        print(f"  Type: {data.get('issue_type', 'N/A')}")
        print()

        print("MATERIALS:")
        for mat in data.get('materials', []):
            print(f"  - {mat['name']} ({mat['category']})")
        print()

        print("TOOLS:")
        for tool in data.get('tools_required', []):
            print(f"  - {tool}")
        print()

        print("REPAIR STEPS:")
        for step in data.get('repair_steps', []):
            print(f"  {step['step']}. {step['title']}")
            print(f"     {step['instruction']}")
            if step.get('safety_tip'):
                print(f"     ⚠️  {step['safety_tip']}")
        print()

        print("WARNINGS:")
        for warning in data.get('warnings', []):
            print(f"  ⚠️  {warning}")
        print()

        session_id = data.get('session_id')
        if session_id:
            print(f"Session ID: {session_id}")
            print("Use this session ID for follow-up questions")
            print()

            # Test follow-up question
            test_followup(session_id, "What tools do I need?", base_url)

    else:
        print("ERROR:")
        print(response.text)


def test_followup(session_id: str, question: str, base_url: str):
    """Test follow-up question."""
    print("-" * 60)
    print("FOLLOW-UP QUESTION:")
    print(f"  Q: {question}")
    print()

    response = requests.post(
        f"{base_url}/diagnose",
        data={'session_id': session_id, 'question': question}
    )

    if response.status_code == 200:
        data = response.json()
        print("RESPONSE:")
        print(f"  {data.get('diagnosis')}")
    else:
        print("ERROR:")
        print(response.text)


def test_health(base_url: str = "http://localhost:8000"):
    """Test health endpoint."""
    response = requests.get(f"{base_url}/health")
    print("HEALTH CHECK:")
    print(response.json())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path>")
        print("Example: python test_api.py broken_toilet.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    test_diagnose(image_path)
