#!/usr/bin/env python3
"""
Analyze webhook payloads from S3 to understand schema
"""
import json
import boto3
from collections import defaultdict, Counter


def analyze_s3_payloads(bucket, prefix='raw/', max_files=100):
    """Analyze webhook payloads from S3"""
    s3 = boto3.client('s3')
    
    print(f"Analyzing payloads in s3://{bucket}/{prefix}")
    print("=" * 60)
    
    # List files
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_files)
    
    if 'Contents' not in response:
        print("No files found")
        return
    
    files = response['Contents']
    print(f"Found {len(files)} files\n")
    
    # Analyze
    field_counts = defaultdict(int)
    field_types = defaultdict(Counter)
    sample_payloads = []
    total = 0
    
    for obj in files[:max_files]:
        try:
            response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            data = json.loads(response['Body'].read())
            
            # Analyze fields
            for key, value in data.items():
                field_counts[key] += 1
                field_types[key][type(value).__name__] += 1
            
            # Save sample
            if len(sample_payloads) < 3:
                sample_payloads.append(data)
            
            total += 1
        except Exception as e:
            print(f"Error reading {obj['Key']}: {e}")
    
    # Print results
    print(f"Analyzed {total} payloads\n")
    
    print("Field Analysis:")
    print("-" * 60)
    for field in sorted(field_counts.keys()):
        count = field_counts[field]
        percentage = (count / total) * 100
        types = ', '.join([f"{t}({c})" for t, c in field_types[field].items()])
        print(f"{field:30} {count:4}/{total} ({percentage:5.1f}%) - {types}")
    
    print("\n" + "=" * 60)
    print("Sample Payloads:")
    print("=" * 60)
    for i, payload in enumerate(sample_payloads, 1):
        print(f"\nSample {i}:")
        print(json.dumps(payload, indent=2)[:500])
    
    # Recommendations
    print("\n" + "=" * 60)
    print("Recommendations:")
    print("=" * 60)
    
    # Find optional fields
    optional = [f for f, c in field_counts.items() if c < total * 0.95]
    if optional:
        print(f"\nOptional fields (< 95% presence):")
        for field in optional:
            print(f"  - {field}")
    
    # Find nested objects
    nested = [f for f, types in field_types.items() if 'dict' in types]
    if nested:
        print(f"\nNested objects (may need flattening):")
        for field in nested:
            print(f"  - {field}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze webhook payloads')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--prefix', default='raw/', help='S3 prefix')
    parser.add_argument('--max', type=int, default=100, help='Max files to analyze')
    
    args = parser.parse_args()
    
    analyze_s3_payloads(args.bucket, args.prefix, args.max)


if __name__ == "__main__":
    main()
