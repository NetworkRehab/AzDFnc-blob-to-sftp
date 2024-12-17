import azure.functions as func
import azure.durable_functions as df
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import paramiko
import logging
import os
from datetime import datetime
import io

async def orchestrator_function(context: df.DurableOrchestrationContext):
    blob_name = context.get_input()
    
    # Get blob content
    blob_content = await context.call_activity('GetBlobContent', blob_name)
    
    # Transfer to SFTP
    result = await context.call_activity('TransferToSftp', {
        'blob_name': blob_name,
        'content': blob_content
    })
    
    return result

async def get_blob_content(blob_name: str) -> bytes:
    connection_string = os.environ['AzureWebJobsStorage']
    container_name = os.environ['BLOB_CONTAINER_NAME']
    
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    
    return await blob_client.download_blob().content_as_bytes()

async def transfer_to_sftp(context):
    blob_name = context['blob_name']
    content = context['content']
    
    # SFTP configuration
    sftp_host = os.environ['SFTP_HOST']
    sftp_port = int(os.environ.get('SFTP_PORT', 22))
    sftp_username = os.environ['SFTP_USERNAME']
    remote_path = os.environ['SFTP_REMOTE_PATH']
    
    # Get SSH key from Key Vault
    keyvault_name = os.environ['KEYVAULT_NAME']
    key_secret_name = os.environ['SSH_KEY_SECRET_NAME']
    keyvault_url = f"https://{keyvault_name}.vault.azure.net"
    
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=keyvault_url, credential=credential)
    private_key_content = secret_client.get_secret(key_secret_name).value
    
    # Setup SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
        ssh.connect(sftp_host, sftp_port, sftp_username, pkey=private_key)
        sftp = ssh.open_sftp()
        
        # Create remote file and write content
        remote_file_path = f"{remote_path}/{blob_name}"
        with sftp.file(remote_file_path, 'wb') as remote_file:
            remote_file.write(content)
            
        return f"Successfully transferred {blob_name} to SFTP"
    
    except Exception as e:
        logging.error(f"Error transferring file: {str(e)}")
        raise
    finally:
        ssh.close()

main = df.Orchestrator.create(orchestrator_function)
get_blob_content = df.Activity.create(get_blob_content)
transfer_to_sftp = df.Activity.create(transfer_to_sftp)
