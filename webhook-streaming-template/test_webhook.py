#!/usr/bin/env python3
"""Test webhook endpoint"""
import json
import argparse
from sa_utils.aws_utilities import test_webhook


def main():
    parser = argparse.ArgumentParser(description='Test webhook endpoint')
    parser.add_argument('--url', required=True, help='Webhook URL')
    parser.add_argument('--count', type=int, default=1, help='Number of tests')
    parser.add_argument('--payload', help='JSON payload file')
    
    args = parser.parse_args()
    
    payload = {}
    if args.payload:
        with open(args.payload) as f:
            payload = json.load(f)
    
    success, failed = test_webhook(args.url, payload, args.count)
    return success == args.count


if __name__ == "__main__":
    exit(0 if main() else 1)
