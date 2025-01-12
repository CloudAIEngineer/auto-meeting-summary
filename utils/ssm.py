import json
import boto3

def get_secret_from_ssm(parameter_name):
    # region_name='eu-central-1'
    ssm_client = boto3.client('ssm')
    response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
    secret_string = response['Parameter']['Value']
    return json.loads(secret_string)