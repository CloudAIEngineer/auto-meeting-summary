import json
import os

def handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_object_key = event['Records'][0]['s3']['object']['key']
    
    print(f"File uploaded to bucket {s3_bucket} with key {s3_object_key}")

    return {
        'statusCode': 200,
        'body': json.dumps('Event processed successfully')
    }
