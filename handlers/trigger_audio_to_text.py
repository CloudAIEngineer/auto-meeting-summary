import boto3
import os

def handler(event, context):
    transcribe = boto3.client('transcribe')

    bucket_name = os.environ['MEETING_BUCKET_NAME']
    transcribe_role_arn = os.environ['TRANSCRIBE_ROLE_ARN']
    file_name = event['Records'][0]['s3']['object']['key']

    job_name = f"transcription-job-{file_name.split('.')[0]}"
    media_uri = f"s3://{bucket_name}/{file_name}"

    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat='mp3',
        LanguageCode='en-US',
        OutputBucketName=os.environ['TRANSCRIPTS_BUCKET_NAME'],
        JobExecutionSettings={'DataAccessRoleArn': transcribe_role_arn}
    )

    return {
        'statusCode': 200,
        'body': 'Transcription job started successfully'
    }
