import boto3
from botocore.exceptions import ClientError
from io import BytesIO
import json


def is_path_s3(path: str) -> bool:
        '''
          Check if the given path is an S3 path.

        :param path: Path to check
        :type path: str
        :return: True if the path is an S3 path, False otherwise
        :rtype: bool
        '''
        return path.startswith("s3://")

def parse_s3_path(s3_path):
    """
    Parse an S3 path into bucket name and object key.

    :param s3_path: S3 path (e.g., s3://bucket-name/object-key)
    :return: Tuple of (bucket_name, object_key)
    """
    if not s3_path.startswith("s3://"):
        raise ValueError("Invalid S3 path. It should start with 's3://'")
    path_parts = s3_path[5:].split("/", 1)
    bucket_name = path_parts[0]
    object_key = path_parts[1] if len(path_parts) > 1 else ""
    return bucket_name, object_key

def read_s3_object(bucket_name, object_key,raw_bytes=True , aws_region=None):
    """
    Read the content of an S3 object (as bytes).

    :param bucket_name: S3 bucket name
    :param object_key: S3 object name (key)
    :param aws_region: (Optional) AWS region
    :return: Object content (bytes) if successful, else None
    """
    s3_client = boto3.client("s3", region_name=aws_region)
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        data =  response["Body"].read()
        if not raw_bytes:
            return BytesIO(data)
        else:
            return data
    except ClientError as e:
        print(f"Failed to read s3://{bucket_name}/{object_key}: {e}")
        return None
    
def save_as_json_to_s3(data, bucket_name, object_key, aws_region=None):
    """
    Save data as a JSON file to an S3 bucket.

    :param data: Data to be saved (should be JSON serializable)
    :param bucket_name: S3 bucket name
    :param object_key: S3 object name (key)
    :param aws_region: (Optional) AWS region
    :return: True if successful, else False
    """

    s3_client = boto3.client("s3", region_name=aws_region)
    json_data = json.dumps(data, indent=2)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=json_data)
        print(f"Data saved to s3://{bucket_name}/{object_key}")
        return True
    except ClientError as e:
        raise Exception(f"Failed to save data to s3://{bucket_name}/{object_key}: {e}")
        

def save_img_to_s3(image_bytes, bucket_name, object_key, aws_region=None):
    """
    Save image bytes to an S3 bucket.

    :param image_bytes: Image data in bytes
    :param bucket_name: S3 bucket name
    :param object_key: S3 object name (key)
    :param aws_region: (Optional) AWS region
    :return: True if successful, else False
    """
    s3_client = boto3.client("s3", region_name=aws_region)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=image_bytes)
        print(f"Image saved to s3://{bucket_name}/{object_key}")
        return True
    except ClientError as e:
        raise Exception(f"Failed to save image to s3://{bucket_name}/{object_key}: {e}")