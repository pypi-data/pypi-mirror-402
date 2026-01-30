__all__ = ['get_boto_s3_client']
import os
import boto3
from minfx.neptune_v2.envs import S3_ENDPOINT_URL

def get_boto_s3_client():
    endpoint_url = os.getenv(S3_ENDPOINT_URL)
    return boto3.resource(service_name='s3', endpoint_url=endpoint_url)