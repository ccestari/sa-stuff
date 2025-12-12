#!/usr/bin/env python3
"""Test webhook endpoint - works with any webhook project"""
import json
import requests
import argparse
from datetime import datetime, timezone

def test_webhook(url, count=1, payload=None):
    print("=" * 60)
    print("Testing Webhook Endpoint")
    print("=" * 60)
    print(f"\nURL: {url}")
    print(f"Tests: {count}")
    
    if not payload:
        payload = {
            "test": True,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "message": "Test webhook"
        }
    
    success_count = 0
    failure_count = 0
    
    for i in range(count):
        try:
            print(f"\n[{i+1}/{count}] Sending webhook...")
            
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Success: {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text}")
                success_count += 1
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                failure_count += 1
                
        except Exception as e:
            print(f"❌ Error: {e}")
            failure_count += 1
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total: {count}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {failure_count}")
    
    return success_count == count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test webhook endpoint')
    parser.add_argument('--url', required=True, help='Webhook URL')
    parser.add_argument('--count', type=int, default=1, help='Number of test webhooks')
    parser.add_argument('--payload', help='JSON payload file path')
    
    args = parser.parse_args()
    
    payload = None
    if args.payload:
        with open(args.payload) as f:
            payload = json.load(f)
    
    test_webhook(args.url, args.count, payload)
