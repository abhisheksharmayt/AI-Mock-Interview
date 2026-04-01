import boto3
import os


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

    def upload_file(self, file_path, bucket_name, key):
        self.s3.upload_file(file_path, bucket_name, key)

    def download_file(self, bucket_name, key, file_path):
        self.s3.download_file(bucket_name, key, file_path)
