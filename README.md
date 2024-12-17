<!--
This file contains the README documentation for the AzDFnc-blob-to-sftp project.
-->
# Azure Durable Function: Blob to SFTP Transfer Guide

A step-by-step guide for cloud administrators new to Python and Azure Functions.

## Overview: Understanding Durable Functions

Azure Durable Functions is an extension of Azure Functions that enables you to write stateful functions in a serverless environment. This project implements a function chaining pattern to orchestrate file transfers.

### Key Concepts

1. **Function Types**
   - **Orchestrator Functions**: Coordinate the workflow
   - **Activity Functions**: Perform the actual work
   - **Client Functions**: Trigger the orchestration

2. **Common Patterns**
   ```
   ┌─────────────────┐     ┌─────────────┐     ┌──────────────┐
   │ HTTP Trigger    │ ──► │ Orchestrator│ ──► │ Activity 1   │
   │ (Start Process) │     │ (Coordinate)│     │ (Get Blob)   │
   └─────────────────┘     └─────────────┘     └──────────────┘
                                │
                                │              ┌──────────────┐
                                └────────────► │ Activity 2   │
                                               │ (SFTP Upload)│
                                               └──────────────┘
   ```

3. **Core Features**
   - **Durability**: Functions can be paused and resumed
   - **State Management**: Automatic checkpointing
   - **Error Handling**: Built-in retry mechanisms

4. **Benefits**
   - Reliable execution in distributed systems
   - Automatic scaling
   - Built-in monitoring
   - Long-running workflows support

### Implementation Details

Our implementation uses:
- **Function Chaining Pattern**: Sequential execution of activities
- **Retry Policies**: Automatic retry on failures
- **Managed Identity**: Secure access to Azure services
- **Key Vault Integration**: Secure secret management

## Table of Contents
1. [Setup and Prerequisites](#setup-and-prerequisites)
2. [Understanding the Code Structure](#understanding-the-code-structure)
3. [Code Breakdown](#code-breakdown)
4. [Deployment Guide](#deployment-guide)
5. [Troubleshooting](#troubleshooting)

## Setup and Prerequisites

### Required Tools
```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Install Python 3.8 or later
# macOS
brew install python@3.8

# Windows
# Download from https://www.python.org/downloads/

# Verify installations
func --version
python --version
```

### Python Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Understanding the Code Structure

### Project Layout
```
📦 AzDFnc-blob-to-sftp
 ┣ 📂 BlobToSftpOrchestrator    # Main orchestrator
 ┣ 📂 GetBlobContent            # Blob storage operations
 ┣ 📂 TransferToSftp           # SFTP transfer logic
 ┗ 📜 requirements.txt         # Python dependencies
```

## Code Breakdown

### Lesson 1: Dependencies
```python
# requirements.txt explained
azure-functions         # Core Azure Functions framework
azure-functions-durable # Enables durable functions pattern
azure-storage-blob     # Azure Blob Storage operations
paramiko              # SFTP client library
azure-keyvault-secrets # Key Vault operations
azure-identity        # Azure authentication
```

### Lesson 2: The Orchestrator Pattern

```python
# BlobToSftpOrchestrator/__init__.py
def orchestrator_function(context):
    # Step 1: Get input blob name
    blob_name = context.get_input()
    
    # Step 2: Configure retry policy
    retry_options = df.RetryOptions(
        first_retry_interval_in_seconds=5,  # Wait 5 seconds before first retry
        max_number_of_attempts=3            # Maximum 3 retry attempts
    )
    
    # Step 3: Download blob content
    blob_content = yield context.call_activity(...)
    
    # Step 4: Transfer to SFTP
    result = yield context.call_activity(...)
```

Key Learning Points:
- Orchestrator coordinates the workflow
- Uses yield for asynchronous operations
- Implements retry policy for resilience

### Lesson 3: Blob Storage Operations

```python
# GetBlobContent/__init__.py key concepts
def main(blob_name: str) -> bytes:
    # 1. Get storage connection
    connection_string = os.environ['AzureWebJobsStorage']
    
    # 2. Create client
    blob_service_client = BlobServiceClient.from_connection_string(...)
    
    # 3. Download blob
    blob_data = blob_client.download_blob().readall()
```

Key Learning Points:
- Uses environment variables for configuration
- Creates blob service client
- Downloads blob content as bytes

### Lesson 4: SFTP Operations with Key Vault

```python
# TransferToSftp/__init__.py key concepts
def main(context):
    # 1. Get SSH key from Key Vault
    credential = DefaultAzureCredential()
    secret_client = SecretClient(...)
    
    # 2. Setup SSH client
    ssh = paramiko.SSHClient()
    private_key = paramiko.RSAKey.from_private_key(...)
    
    # 3. Transfer file
    sftp = ssh.open_sftp()
    with sftp.file(remote_path, 'wb') as remote_file:
        remote_file.write(content)
```

Key Learning Points:
- Uses managed identity for Key Vault access
- Handles SSH key authentication
- Manages SFTP file transfer

## Deployment Guide

### Step 1: Azure Resources Setup
```bash
# Create resource group
az group create --name MyFuncGroup --location eastus

# Create storage account
az storage account create \
    --name mystorage \
    --resource-group MyFuncGroup \
    --sku Standard_LRS

# Create function app
az functionapp create \
    --name MyBlobToSftpFunc \
    --resource-group MyFuncGroup \
    --storage-account mystorage \
    --runtime python \
    --runtime-version 3.8 \
    --consumption-plan-location eastus
```

### Step 2: Key Vault Setup
```bash
# Create Key Vault
az keyvault create \
    --name mykeyvault \
    --resource-group MyFuncGroup \
    --location eastus

# Store SSH private key
az keyvault secret set \
    --vault-name mykeyvault \
    --name sftp-private-key \
    --file ~/.ssh/id_rsa
```

### Step 3: Configure Function App Settings
```bash
# Configure app settings
az functionapp config appsettings set \
    --name MyBlobToSftpFunc \
    --resource-group MyFuncGroup \
    --settings @local.settings.json
```

### Step 4: Enable Managed Identity
```bash
# Enable system-assigned managed identity
az functionapp identity assign \
    --name MyBlobToSftpFunc \
    --resource-group MyFuncGroup

# Grant Key Vault access
az keyvault set-policy \
    --name mykeyvault \
    --object-id <identity-object-id> \
    --secret-permissions get
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
```python
# Check if managed identity is enabled
print(os.environ.get('AZURE_CLIENT_ID'))  # Should not be None

# Verify Key Vault access
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
# If this fails, check managed identity setup
```

2. **SFTP Connection Issues**
```python
# Enable detailed SSH logging
import logging
logging.getLogger('paramiko').setLevel(logging.DEBUG)
```

3. **Blob Storage Access**
```python
# Verify storage connection
from azure.storage.blob import BlobServiceClient
client = BlobServiceClient.from_connection_string(conn_string)
containers = client.list_containers()
# Should list available containers
```

### Monitoring

1. **View Function Logs**
```bash
az functionapp logs tail \
    --name MyBlobToSftpFunc \
    --resource-group MyFuncGroup
```

2. **Check Function Status**
```bash
az functionapp show \
    --name MyBlobToSftpFunc \
    --resource-group MyFuncGroup
```

## Security Best Practices

1. **Never Store Credentials in Code**
   - Use Key Vault for secrets
   - Use managed identities
   - Configure RBAC appropriately

2. **Network Security**
   - Use private endpoints where possible
   - Restrict inbound/outbound traffic
   - Enable FTPS if supported

3. **Monitoring**
   - Enable Application Insights
   - Set up alerts for failures
   - Monitor Key Vault access logs

## Next Steps

1. Set up CI/CD pipeline
2. Configure monitoring and alerts
3. Implement disaster recovery plan
4. Document operational procedures

For additional support, refer to:
- [Azure Functions Python Developer Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Durable Functions Documentation](https://docs.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview?tabs=python)