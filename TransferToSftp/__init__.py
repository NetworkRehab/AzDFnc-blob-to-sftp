import os
import io
import logging
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import paramiko

def main(context):
    blob_name = context['blob_name']
    content = context['content']
    
    # SFTP configuration
    sftp_host = os.environ['SFTP_HOST']
    sftp_port = int(os.environ['SFTP_PORT'])
    sftp_username = os.environ['SFTP_USERNAME']
    remote_path = os.environ['SFTP_REMOTE_PATH']
    
    # Get SSH key from Key Vault
    keyvault_name = os.environ['KEYVAULT_NAME']
    ssh_key_secret_name = os.environ['SSH_KEY_SECRET_NAME']
    keyvault_url = f"https://{keyvault_name}.vault.azure.net"
    
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=keyvault_url, credential=credential)
    private_key_content = secret_client.get_secret(ssh_key_secret_name).value
    
    # Setup SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_content))
        ssh.connect(hostname=sftp_host, port=sftp_port, username=sftp_username, pkey=private_key)
        sftp = ssh.open_sftp()
        
        # Create remote file and write content
        remote_file_path = f"{remote_path}/{blob_name}"
        with sftp.file(remote_file_path, 'wb') as remote_file:
            remote_file.write(content)
        
        return f"Successfully transferred {blob_name} to SFTP"
    
    except Exception as e:
        logging.error(f"Error transferring file: {e}")
        raise
    
    finally:
        ssh.close()