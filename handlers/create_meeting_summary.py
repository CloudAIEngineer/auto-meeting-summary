import boto3
import os
import requests

def lambda_handler(event, context):
    sns_message = event['Records'][0]['Sns']['Message']
    transcribe = boto3.client('transcribe')
    s3 = boto3.client('s3')
    bedrock = boto3.client('bedrock')
    confluence_url = os.environ['CONFLUENCE_API_URL']
    confluence_api_key = os.environ['CONFLUENCE_API_KEY']

    job_name = sns_message['TranscriptionJobName']
    transcript_uri = sns_message['Transcript']['TranscriptFileUri']
    
    bucket_name = transcript_uri.split('/')[2]
    transcript_key = '/'.join(transcript_uri.split('/')[3:])

    transcript_object = s3.get_object(Bucket=bucket_name, Key=transcript_key)
    transcript_text = transcript_object['Body'].read().decode('utf-8')

    prompt_template = get_prompt_template()

    response = bedrock.invoke_model(
        modelId="amazon.titan.large",
        body={
            "input": prompt_template.format(job_name=job_name, transcript_text=transcript_text)
        }
    )

    confluence_page_content = response['body']
    create_confluence_page(confluence_url, confluence_api_key, confluence_page_content)

    return {
        'statusCode': 200,
        'body': 'Meeting summary successfully created in Confluence'
    }

def get_prompt_template():
    file_path = os.path.join(os.path.dirname(__file__), 'prompt_template.txt')
    with open(file_path, 'r') as file:
        return file.read()

def create_confluence_page(url, api_key, content):
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "page",
        "title": "Meeting Summary",
        "space": {"key": "YOUR_SPACE_KEY"},
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }
    response = requests.post(url + "/rest/api/content/", headers=headers, json=data)
    return response