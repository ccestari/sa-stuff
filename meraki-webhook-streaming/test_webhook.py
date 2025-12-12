#!/usr/bin/env python3
"""
Test Meraki webhook endpoint
"""
import json
import requests
import argparse
from datetime import datetime

def load_sample_payload():
    """Load sample Meraki webhook payload"""
    return {
        "version": "0.1",
        "sharedSecret": "test_secret_123",
        "sentAt": datetime.utcnow().isoformat() + "Z",
        "organizationId": "25998",
        "organizationName": "Success Charter Network",
        "organizationUrl": "https://n14.dashboard.meraki.com/o/03ni7a/manage/organization/overview",
        "networkId": "L_570831252769210967",
        "networkName": "TEST-NETWORK",
        "networkUrl": "https://n14.dashboard.meraki.com/TEST-NETWORK/n/test/manage/nodes/list",
        "networkTags": [],
        "deviceSerial": "Q3CA-TEST-1234",
        "deviceMac": "bc:33:40:ff:c9:e7",
        "deviceName": "TEST-DEVICE-001",
        "deviceUrl": "https://n14.dashboard.meraki.com/TEST-NETWORK/n/test/manage/nodes/new_list/123456",
        "deviceTags": ["test", "demo"],
        "deviceModel": "MT10",
        "alertId": "999999999999999999",
        "alertType": "Sensor change detected",
        "alertTypeId": "sensor_alert",
        "alertLevel": "informational",
        "occurredAt": datetime.utcnow().isoformat() + "Z",
        "alertData": {
            "alertConfigId": 123456789,
            "alertConfigName": "Test Temperature Threshold",
            "triggerData": [{
                "conditionId": 987654321,
                "trigger": {
                    "ts": datetime.utcnow().timestamp(),
                    "type": "temperature",
                    "nodeId": 111222333,
                    "sensorValue": 21.5
                }
            }],
            "startedAlerting": True
        }
    }

def test_webhook(url, count=1):
    """Test webhook endpoint with sample data"""
    print("=" * 60)
    print("Testing Meraki Webhook Endpoint")
    print("=" * 60)
    print(f"\nURL: {url}")
    print(f"Tests: {count}")
    
    success_count = 0
    failure_count = 0
    
    for i in range(count):
        try:
            payload = load_sample_payload()
            
            print(f"\n[{i+1}/{count}] Sending webhook...")
            
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Success: {response.status_code}")
                print(f"   Response: {response.json()}")
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

def main():
    parser = argparse.ArgumentParser(description='Test Meraki webhook endpoint')
    parser.add_argument('--url', help='Webhook URL', default=None)
    parser.add_argument('--count', type=int, help='Number of test webhooks to send', default=1)
    
    args = parser.parse_args()
    
    # Load deployment info if URL not provided
    if not args.url:
        try:
            with open('deployment_info.json') as f:
                deployment_info = json.load(f)
                args.url = deployment_info['api_url']
        except FileNotFoundError:
            print("❌ No deployment_info.json found. Please provide --url or deploy first.")
            return False
    
    return test_webhook(args.url, args.count)

if __name__ == "__main__":
    main()
