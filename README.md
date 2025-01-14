# Meeting Summary Service

This project provides a serverless pipeline to transcribe and summarize meeting recordings using AWS Lambda, S3, and Confluence. Audio files are uploaded to S3, transcribed by AWS Transcribe, and summarized with an LLM model. The summary is then posted to Confluence.

## Features:
- **Audio transcription** using AWS Transcribe.
- **Summary generation** using a Large Language Model (LLM).
- **S3 trigger** automatically processes audio files as they are uploaded to the S3 bucket.
- **Lambda functions** handle audio processing, transcription, and summary creation.
- **Confluence API** posts the generated meeting summary.

## Architecture Overview:
- **TriggerAudioToText**: A Lambda function that triggers transcription when an audio file is uploaded to the `meeting-records` S3 bucket.
- **CreateMeetingSummary**: A Lambda function that generates a summary from the transcription and posts it to Confluence.
- **S3 Buckets**: Used for storing meeting audio files and transcriptions.
- **Confluence API**: Used to create and publish a meeting summary page in Confluence.

## Workflow:
1. **Audio Upload to S3**: Upload an audio file containing a meeting recording to the `meeting-records` S3 bucket.
2. **Transcription**: The `TriggerAudioToText` Lambda function is triggered to transcribe the audio using AWS Transcribe.
3. **Summary Creation**: The `CreateMeetingSummary` Lambda function is triggered by the transcription output. It generates a summary and posts it to Confluence.

## Setup

### Prerequisites:
- **Serverless Framework** installed.
- AWS CLI configured with appropriate credentials.
- S3 buckets created for meeting audio files and transcripts (specified in the Serverless configuration).
- **Confluence API credentials** must be stored in AWS Parameter Store in the following format:

```json
{
    "email": "your-email@example.com",
    "api_token": "YOUR_API_TOKEN_HERE",
    "space_key": "YOUR_SPACE_KEY_HERE"
}
```
Ensure that the **Confluence API credentials** are available in your AWS Parameter Store as they will be used by the Lambda functions to interact with Confluence.

### Install Dependencies:
1. Clone this repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies (for Serverless framework):
   ```bash
   npm install
   ```

4. Deploy the service to AWS:
   ```bash
   serverless deploy
   ```

### S3 Buckets:
- **meeting-records**: Stores audio files to be transcribed.
- **meeting-transcripts**: Stores transcribed text files.

### Lambda Functions:
- **TriggerAudioToText**: Triggers when a new file is uploaded to `meeting-records`, transcribing the audio to text.
- **CreateMeetingSummary**: Generates a meeting summary and posts it to Confluence.

## Resources:
- **IAM Roles**: Permissions for Lambda functions to access S3, Transcribe, and Confluence API.
- **Parameter Store**: Used to store sensitive information such as Confluence API keys and secrets.

## License
This project is licensed under the MIT License.