import boto3
import os
from io import BytesIO

class AmazonUtils:

    def __init__(self):
        if os.getenv("ENV", "dev") == "dev":
            self.s3 = boto3.client(
                "s3",
                endpoint_url="http://localhost:9000",
                aws_access_key_id="minio",
                aws_secret_access_key="minio123",
            )
        else:
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION"),
            )

    def upload_file_as_object(self, data, bucket_name: str, key: str) -> None:
        self.s3.upload_fileobj(data, bucket_name, key)

    def delete_object(self, bucket_name: str, key: str) -> None:
        """Remove an object; used to roll back uploads when DB persistence fails."""
        self.s3.delete_object(Bucket=bucket_name, Key=key)

    def download_file_as_bytes(self, bucket_name: str, key: str) -> bytes:
        response = self.s3.get_object(Bucket=bucket_name, Key=key)
        return response["Body"].read()
