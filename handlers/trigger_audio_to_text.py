import boto3
import os

def trigger_audio_to_text(event, context):
    transcribe = boto3.client('transcribe')

    bucket_name = os.environ['MEETING_BUCKET_NAME']
    file_name = event['Records'][0]['s3']['object']['key']

    job_name = f"transcription-job-{file_name.split('.')[0]}"
    job_uri = f"s3://{bucket_name}/{file_name}"

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='mp3',
        LanguageCode='en-US',
        OutputBucketName=os.environ['TRANSCRIPTS_BUCKET_NAME'],
        NotificationChannel={
            'RoleArn': os.environ['TRANSCRIBE_ROLE_ARN'],
            'SNSTopicArn': os.environ['SNS_TOPIC_ARN']
        }
    )

    return {
        'statusCode': 200,
        'body': 'Transcription job started successfully'
    }
