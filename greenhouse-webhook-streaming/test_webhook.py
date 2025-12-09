"""
Test webhook endpoint
Useful for verifying Lambda is working
"""
import requests
import json
import sys

def test_webhook(url, payload=None, count=1):
    """Test webhook endpoint with optional payload"""
    
    if payload is None:
        payload = {}
    
    print(f"Testing webhook: {url}")
    print(f"Payload: {json.dumps(payload)}")
    print(f"Count: {count}")
    print("-" * 80)
    
    success = 0
    failed = 0
    
    for i in range(count):
        try:
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                success += 1
                print(f"[{i+1}] SUCCESS - Status: {response.status_code}")
                print(f"    Response: {response.text}")
            else:
                failed += 1
                print(f"[{i+1}] FAILED - Status: {response.status_code}")
                print(f"    Response: {response.text}")
                
        except Exception as e:
            failed += 1
            print(f"[{i+1}] ERROR - {e}")
    
    print("-" * 80)
    print(f"Results: {success} success, {failed} failed")
    return success, failed

if __name__ == '__main__':
    # Default endpoint
    url = 'https://kac177dcb8.execute-api.us-east-1.amazonaws.com/prod/webhook'
    
    # Parse command line args
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("Usage: python test_webhook.py [--url URL] [--count N]")
            sys.exit(0)
        elif sys.argv[1] == '--url':
            url = sys.argv[2]
        elif sys.argv[1] == '--count':
            count = int(sys.argv[2])
    
    # Test with empty payload
    test_webhook(url, payload={}, count=1)
    
    # Test with sample payload
    sample_payload = {
        "action": "application_updated",
        "payload": {
            "application": {
                "id": 12345,
                "candidate": {
                    "id": 67890,
                    "first_name": "Test",
                    "last_name": "User"
                }
            }
        }
    }
    
    print("\nTesting with sample payload...")
    test_webhook(url, payload=sample_payload, count=1)
