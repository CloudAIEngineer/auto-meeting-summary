import json
import boto3
import os
import re
from utils.prompt import extract_meeting_summary
from utils.confluence import create_confluence_page
from utils.ssm import get_secret_from_ssm

def handler(event, context):
    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_object_key = event['Records'][0]['s3']['object']['key']
    #s3_bucket = 'meeting-transcripts-20250108'
    #s3_object_key = 'transcription-job-Kevin-Surace-1-Minute-Ted-Talk.json'
    
    s3_client = boto3.client('s3')
    
    file_obj = s3_client.get_object(Bucket=s3_bucket, Key=s3_object_key)
    file_content = json.loads(file_obj['Body'].read().decode('utf-8'))
    response_body = extract_meeting_summary(file_content['results']['audio_segments'])
    print(response_body)
    #response_body = {'type': 'completion'}

    if response_body.get('type') == 'completion':
        completion_text = response_body.get('completion')
        '''file_path = os.path.join(os.path.dirname(__file__), 'resp.txt')
        with open(file_path, 'r') as file:
            completion_text = file.read()'''
        print(f"Completion: {completion_text}")
        match = re.search(r'```json\s*(\{.*\})\s*```', completion_text, re.DOTALL)
        if match:
            #print(f"Match is {match}")
            json_string = match.group(1)
            parsed_json = json.loads(json_string)
            confluence_secret = get_secret_from_ssm(os.environ['CONFLUENCE_API_SECRET'])
            response = create_confluence_page(parsed_json, os.environ['CONFLUENCE_API_URL'], confluence_secret)
            print(response)
            if response.status_code == 200:
                return {
                    'statusCode': 200,
                    'body': 'Confluence page created successfully'
                }
            else:
                return {
                    'statusCode': response.status_code,
                    'body': f"Failed to create Confluence page: {response.text}"
                }                
        else:
            print(f"No JSON match found in the completion text. Raw completion text: {completion_text}")