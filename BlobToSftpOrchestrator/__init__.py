import azure.durable_functions as df

def orchestrator_function(context: df.DurableOrchestrationContext):
    blob_name = context.get_input()

    # Retry policy
    retry_options = df.RetryOptions(first_retry_interval_in_seconds=5, max_number_of_attempts=3)

    # Get blob content
    blob_content = yield context.call_activity('GetBlobContent', blob_name, retry_options=retry_options)

    # Transfer to SFTP
    result = yield context.call_activity('TransferToSftp', {
        'blob_name': blob_name,
        'content': blob_content
    }, retry_options=retry_options)

    return result

main = df.Orchestrator.create(orchestrator_function)