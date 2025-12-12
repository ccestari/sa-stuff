#!/usr/bin/env python3
"""Check Lambda CloudWatch logs"""
import json
import argparse
from sa_utils.aws_utilities import get_lambda_logs


def main():
    parser = argparse.ArgumentParser(description='Check Lambda logs')
    parser.add_argument('--function', help='Lambda function name')
    parser.add_argument('--hours', type=int, default=1, help='Hours to look back')
    parser.add_argument('--limit', type=int, default=50, help='Max events per stream')
    
    args = parser.parse_args()
    
    # Load function name from config if not provided
    if not args.function:
        with open('config.json') as f:
            config = json.load(f)
            args.function = config['lambda']['function_name']
    
    get_lambda_logs(args.function, args.hours, args.limit)


if __name__ == "__main__":
    main()
