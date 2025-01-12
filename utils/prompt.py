import json
import boto3
import os

def extract_meeting_summary(audio_segments):
    processed_segments = []

    for segment in audio_segments:
        processed_segment = {
            "start_time": segment['start_time'],
            "end_time": segment['end_time'],
            "transcript": segment['transcript']
        }
        processed_segments.append(processed_segment)
    
    template_file_path = os.path.join(os.path.dirname(__file__), "./prompt_template.txt")

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
    
    return json.loads(response.get('body').read())