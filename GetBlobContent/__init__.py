import os
from azure.storage.blob import BlobServiceClient

def main(blob_name: str) -> bytes:
    connection_string = os.environ['AzureWebJobsStorage']
    container_name = os.environ['BLOB_CONTAINER_NAME']

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container_name, blob_name)
    blob_data = blob_client.download_blob().readall()

    return blob_data