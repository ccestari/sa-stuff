"""
Fetch and display Lambda CloudWatch logs
Utility for monitoring Lambda execution
"""
import boto3
from datetime import datetime, timedelta

def get_lambda_logs(function_name, hours=1, limit=50):
    """Fetch recent Lambda logs from CloudWatch"""
    
    logs = boto3.client('logs', region_name='us-east-1')
    log_group = f'/aws/lambda/{function_name}'
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    print(f"Fetching logs for: {function_name}")
    print(f"Time range: {start_time} to {end_time} UTC")
    print(f"Log group: {log_group}")
    print("=" * 80)
    
    try:
        # Get log streams
        streams_response = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response.get('logStreams'):
            print("[WARNING] No log streams found")
            return
        
        # Get events from recent streams
        for stream in streams_response['logStreams']:
            stream_name = stream['logStreamName']
            print(f"\nStream: {stream_name}")
            print("-" * 80)
            
            events_response = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                limit=limit
            )
            
            for event in events_response.get('events', []):
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                print(f"[{timestamp}] {message}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"[ERROR] {e}")
        print("\nMake sure you have AWS credentials configured and permissions to read CloudWatch logs")

if __name__ == '__main__':
    function_name = 'greenhouse-webhook-processor'
    get_lambda_logs(function_name, hours=24, limit=100)
