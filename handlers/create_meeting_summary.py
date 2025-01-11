import json
import boto3
import os
import re
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

def handler(event, context):
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
    
    template_file_path = os.path.join(os.path.dirname(__file__), "../config/prompt_template.txt")

    with open(template_file_path, 'r') as template_file:
        prompt_template = template_file.read()

    prompt = prompt_template.replace("{audio_segments}", json.dumps({"audio_segments": processed_segments}, indent=2))

    bedrock = boto3.client(service_name='bedrock-runtime')
    response = bedrock.invoke_model(
        modelId="anthropic.claude-v2:1",
        body=json.dumps({
            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
            "max_tokens_to_sample": 3000
        }),
        contentType='application/json'
    )
    
    response_body = json.loads(response.get('body').read())
    print('response')
    print(response_body)

    if response_body.get('type') == 'completion':
        completion_text = response_body.get('completion')
        print('Completion')
        print(completion_text)
        match = re.search(r'```json\s*(\{.*\})\s*```', completion_text, re.DOTALL)
        if match:
            json_string = match.group(1)
            parsed_json = json.loads(json_string)
            print(parsed_json)
        else:
            print('No match')

def get_secret_from_ssm(parameter_name):
    ssm_client = boto3.client('ssm')
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    secret_string = response['Parameter']['Value']
    return json.loads(secret_string)

def create_confluence_page(meeting_data):
    confluence_url = os.environ['CONFLUENCE_API_URL']
    confluence_secret = get_secret_from_ssm(os.environ['CONFLUENCE_API_SECRET'])
    auth = (confluence_secret['email'], confluence_secret['api_token'])

    # Get current date in the desired format
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Build the page content
    page_title = f"Meeting Minutes - {current_date}"

    # Create HTML structure using xml.etree.ElementTree
    root = ET.Element("html")
    body = ET.SubElement(root, "body")

    h2 = ET.SubElement(body, "h2")
    h2.text = "Meeting Minutes"

    date_paragraph = ET.SubElement(body, "p")
    date_paragraph.text = f"Date: {current_date}"

    participants_paragraph = ET.SubElement(body, "p")
    participants_paragraph.text = f"Participants: {', '.join(meeting_data.get('Participants', []))}"

    goals_paragraph = ET.SubElement(body, "p")
    goals_paragraph.text = f"Goals: {meeting_data.get('Goals', 'N/A')}"

    # Discussion Topics Table
    discussion_topics_header = ET.SubElement(body, "h3")
    discussion_topics_header.text = "Discussion Topics"
    table = ET.SubElement(body, "table")

    # Table headers
    header_row = ET.SubElement(table, "tr")
    headers = ["Time", "Item", "Presenter", "Notes"]
    for header in headers:
        th = ET.SubElement(header_row, "th")
        th.text = header

    # Add table rows for each discussion topic
    for topic in meeting_data.get('DiscussionTopics', []):
        row = ET.SubElement(table, "tr")
        for key in headers:
            td = ET.SubElement(row, "td")
            td.text = topic.get(key, 'N/A') if key != 'Presenter' else topic.get('Presenter', '')

    # Action Items List
    action_items_header = ET.SubElement(body, "h3")
    action_items_header.text = "Action Items"
    action_items_list = ET.SubElement(body, "ul")
    for item in meeting_data.get('ActionItems', []):
        li = ET.SubElement(action_items_list, "li")
        li.text = item

    # Decisions List
    decisions_header = ET.SubElement(body, "h3")
    decisions_header.text = "Decisions"
    decisions_list = ET.SubElement(body, "ul")
    for decision in meeting_data.get('Decisions', []):
        li = ET.SubElement(decisions_list, "li")
        li.text = decision

    html_content = ET.tostring(root, encoding='unicode')

    storage_format_content = {
        "type": "page",
        "title": page_title,
        "body": {
            "storage": {
                "value": html_content,
                "representation": "storage"
            }
        }
    }

    response = requests.post(confluence_url, json=storage_format_content, auth=auth, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print("Confluence page created successfully!")
        return response.json()
    else:
        print(f"Failed to create Confluence page: {response.status_code}, {response.text}")
        return None