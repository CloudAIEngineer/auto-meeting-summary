import json
import boto3

def handler(event, context):
    #print("Received event:", json.dumps(event, indent=2))

    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_object_key = event['Records'][0]['s3']['object']['key']
    
    s3_client = boto3.client('s3')
    
    file_obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_object_key)
    file_content = json.loads(file_obj['Body'].read().decode('utf-8'))

    audio_segments = file_content['results']['audio_segments']
    processed_segments = []

    for segment in audio_segments:
        processed_segment = {
            "start_time": segment['start_time'],
            "end_time": segment['end_time'],
            "transcript": segment['transcript']
        }
        processed_segments.append(processed_segment)
    
    print(json.dumps(processed_segments, indent=2))

    return {
        'statusCode': 200,
        'body': json.dumps('Event processed successfully')
    }