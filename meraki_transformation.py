import base64
#import yaml
import logging
import polars as pl

print('Loading function')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    output = []
    global rename_cols
    global convert_str_datetime


    output_records = []
    print(f"Received {len(event.get('records', []))} records to process.")

    for record in event.get('records', []):
        record_id = record.get('recordId')
        
        try:
            # 1. Decode the incoming data from base64
            # The data from Firehose is base64 encoded.
            payload_decoded = base64.b64decode(record.get('data', '')).decode('utf-8')

            # It's common for multiple JSON objects to be sent in a single payload,
            # separated by newlines.
            if not payload_decoded.strip():
                print(f"Record {record_id} has empty payload, marking as Dropped.")
                output_records.append({'recordId': record_id, 'result': 'Dropped', 'data': record.get('data','')})
                continue
                
            json_data = [json.loads(line) for line in payload_decoded.strip().split('\n')]

            # 2. Load data into a Polars DataFrame for efficient transformation
            df = pl.read_ndjson(json_data)

            # 3. --- YOUR TRANSFORMATION LOGIC GOES HERE ---
            logger.info(f'Created DataFrame')
            df = df.unnest('payload').unnest('alertData').explode('triggerData').unnest('triggerData').unnest('trigger')
            logger.info(f'Unnested DataFrame')
            df = df.rename(rename_cols)
            logger.info(f'Renamed DataFrame')
            print(df)
            
            
            df_transformed = df.with_columns([
                pl.col("event_timestamp").str.to_datetime("%Y-%m-%dT%H:%M:%S%.f", strict=False),
                pl.col("price").cast(pl.Float64),
                pl.lit(datetime.utcnow().isoformat()).alias("processing_ts")
            ])
            
            
            records_as_dicts = df.to_dicts()
            transformed_payload_str = "\n".join(json.dumps(d, default=str) for d in records_as_dicts) + "\n"

            # 5. Encode the transformed data back to base64
            payload_encoded = base64.b64encode(transformed_payload_str.encode('utf-8')).decode('utf-8')
            
            # 6. Append the processed record to the output list
            output_records.append({
                'recordId': record_id,
                'result': 'Ok',
                'data': payload_encoded
            })

        except Exception as e:
            # If any step in the transformation fails, mark the record as
            # 'ProcessingFailed' and return the original data. Firehose can be
            # configured to route these failed records to a separate S3 bucket
            # for later inspection and reprocessing.
            print(f"Error processing record {record_id}: {str(e)}")
            output_records.append({
                'recordId': record_id,
                'result': 'ProcessingFailed',
                'data': record.get('data', '') # Return original data
            })

    print(f"Successfully processed {len(output_records)} records.")
    return {'records': output_records}




'''
    logger.info(f'Event: {event}')

    #for record in event['records']:
    for record in event:
        logger.info(f'Entered for loop: {record}')
        #print(record['recordId'])
        payload = base64.b64decode(record['data']).decode('utf-8')

        logger.info(f'Entering DataFrame Build - Payload: {payload}')

        # Do custom processing on the payload here
        df = pl.read_ndjson(payload)
        logger.info(f'Created DataFrame')
        df = df.unnest('payload').unnest('alertData').explode('triggerData').unnest('triggerData').unnest('trigger')
        logger.info(f'Unnested DataFrame')
        df = df.rename(rename_cols)
        logger.info(f'Renamed DataFrame')
        #print(df)

        
        # Error caused by timestamp string containing '.' that cannot be converted by rust's chrono crate
        # To fix later
        #for col in convert_str_datetime:
        #    df = convert_str_to_dateteime(df, col)

        payload = df.write_ndjson()


    output_record = {
        'recordId': record['recordId'],
        'result': 'Ok',
        'data': base64.b64encode(payload.encode('utf-8')).decode('utf-8')
    }
    output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}

def convert_str_to_dateteime(df: pl.DataFrame, col: str) -> pl.DataFrame:
    df = df.with_columns(pl.col(col).str.strptime(pl.Datetime, '%Y-%m-%dT%H:%M:%S.%fZ'))
    return df
'''
rename_cols = {
    'timestamp': 'alert_timestamp'
    , 'source': 'alert_source'
    , 'version': 'webhook_version'
    , 'sharedSecret': 'shared_secret'
    , 'sentAt': 'alert_sent_at'
    , 'organizationId': 'organization_id'
    , 'organizationName': 'organization_name'
    , 'organizationUrl': 'organization_url'
    , 'networkId': 'network_id'
    , 'networkName': 'network_name'
    , 'networkUrl': 'network_url'
    , 'deviceSerial': 'device_serial'
    , 'deviceMac': 'device_mac'
    , 'deviceName': 'device_name'
    , 'deviceUrl': 'device_url'
    , 'deviceTags': 'device_tags'
    , 'deviceModel': 'device_model'
    , 'alertId': 'alert_id'
    , 'alertType': 'alert_type'
    , 'alertTypeId': 'alert_type_id'
    , 'alertLevel': 'alert_level'
    , 'occurredAt': 'alert_occurrred_at'
    , 'alertConfigId': 'alert_config_id'
    , 'alertConfigName': 'alert_config_name'
    , 'conditionId': 'condition_id'
    , 'ts': 'event_timestamp'
    , 'type': 'sensor_type'
    , 'nodeId': 'node_id'
    , 'sensorValue': 'sensor_value'
    , 'startedAlerting': 'started_alerting'
}

convert_str_datetime = [
    'alert_timestamp'
    , 'alert_sent_at'
    , 'alert_occurrred_at'
]