import base64
import json
import gzip
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    output = []
    
    for record in event['records']:
        record_id = record['recordId']
        logger.info(f"RecordId is: {record_id}")
        
        try:
            # Decode base64 data
            compressed_payload = base64.b64decode(record['data'])
            
            # Try to decompress if it's gzipped
            try:
                payload = gzip.decompress(compressed_payload).decode('utf-8')
                logger.info("Successfully decompressed gzipped data")
            except (gzip.BadGzipFile, OSError):
                # If not gzipped, try direct UTF-8 decode
                try:
                    payload = compressed_payload.decode('utf-8')
                    logger.info("Successfully decoded as UTF-8")
                except UnicodeDecodeError:
                    # If UTF-8 fails, try latin-1 (which accepts any byte sequence)
                    payload = compressed_payload.decode('latin-1')
                    logger.info("Decoded using latin-1 fallback")
            
            # Parse JSON if possible
            try:
                data = json.loads(payload)
                logger.info(f"Successfully parsed JSON: {json.dumps(data)[:200]}...")
            except json.JSONDecodeError:
                # If not valid JSON, treat as raw string
                data = {"raw_data": payload, "timestamp": context.aws_request_id}
                logger.info("Treating as raw string data")
            
            # Add processing timestamp
            if isinstance(data, dict):
                data['processed_at'] = context.aws_request_id
            
            # Convert back to JSON string
            output_data = json.dumps(data) + '\n'
            
            # Encode back to base64
            output_record = {
                'recordId': record_id,
                'result': 'Ok',
                'data': base64.b64encode(output_data.encode('utf-8')).decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Error processing record {record_id}: {str(e)}")
            # Return the record as failed for retry
            output_record = {
                'recordId': record_id,
                'result': 'ProcessingFailed'
            }
        
        output.append(output_record)
    
    logger.info(f"Processed {len(output)} records")
    return {'records': output}