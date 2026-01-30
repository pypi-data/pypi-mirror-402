import boto3


def fetch_password_from_ssm(name):
    ssm = boto3.client('ssm')
    ssm_obj = ssm.get_parameter(Name=name, WithDecryption=True)
    return ssm_obj['Parameter']['Value']
