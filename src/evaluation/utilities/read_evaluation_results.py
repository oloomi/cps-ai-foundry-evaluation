import os
import json
from azure.identity import DefaultAzureCredential
from azure.mgmt.machinelearningservices import AzureMachineLearningWorkspaces
from storage_account_util import read_blob_from_uri


def get_workspace_specs():
    """Get workspace specifications."""
    credential = DefaultAzureCredential()
    subscription_id = os.environ["SUBSCRIPTION_ID"]
    resource_group_name = os.environ["RESOURCE_GROUP"]
    workspace_name = os.environ["AI_FOUNDRY_PROJECT_NAME"]

    ml_client = AzureMachineLearningWorkspaces(credential, subscription_id)
    workspace = ml_client.workspaces.get(resource_group_name, workspace_name)
    # Extract project/workspace ID
    project_id = workspace.workspace_id
    # Extract storage account name
    storage_id = workspace.storage_account
    storage_account_name = storage_id.split("/")[-1] if storage_id else None

    return {
        "project_id": project_id,
        "storage_account_name": storage_account_name,
    }


def get_evaluation_results(evaluation_response):
    """
    Get evaluation results from AI Hub Project evaluation runs.

    Args:
        evaluation_response: The response object from evaluations.create method.

    Returns:
        Parsed JSON content of the evaluation results.
    """
    try:
        # Get workspace specifications
        workspace_specs = get_workspace_specs()
        workspace_id = workspace_specs["project_id"]
        storage_account_name = workspace_specs["storage_account_name"]

        # Construct the results URI
        job_id = evaluation_response.id
        data_container_id = f"dcid.{job_id}"
        results_uri = f"https://{storage_account_name}.blob.core.windows.net/{workspace_id}-azureml/ExperimentRun/{data_container_id}/instance_results.jsonl"

        # Read the blob content
        content = read_blob_from_uri(results_uri)

        if content:
            # Parse JSONL content
            lines = content.strip().split("\n")
            results = []

            for line in lines:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Error parsing line: {e}")
                        continue

            print(f"Parsed {len(results)} JSON objects")
            return results
        else:
            print("Failed to read blob content")

    except Exception as e:
        print(f"Error processing evaluation response: {e}")
        return None
