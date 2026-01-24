# n8n Workflow Setup: AWS to Smart Vault

This workflow automates the ingestion of evidence files from an AWS S3 bucket directly into the Naya Judicial System.

## Prerequisites
- [n8n](https://n8n.io/) installed locally or cloud account.
- AWS S3 Bucket (e.g., `naya-judicial-evidence`).
- AWS Access Key and Secret Key.

## Installation

1.  **Import Workflow**
    - Open n8n Dashboard.
    - Click **Workflow** > **Import from File...**
    - Select `workflows/aws_ingestion_workflow.json`.

2.  **Configure Credentials**
    - Double click the **AWS S3 List** node.
    - Under credentials, select **Create New** -> **AWS**.
    - Enter your `Access Key ID` and `Secret Access Key`.
    - Do the same for the **AWS S3 Download** node.

3.  **Configure Bucket**
    - In **AWS S3 List** and **AWS S3 Download** nodes, change `bucketName` to your actual S3 bucket name if different.

4.  **Activate**
    - Toggle **Active** switch in the top right.
    - The workflow will now check for new files every 15 minutes.
    - Files named like `CASE-123_evidence.pdf` will be automatically uploaded to the specific case Vault.

## How it Works
1.  **Scheduler**: Triggers every 15 mins.
2.  **S3 List**: Checks for object keys in the bucket.
3.  **S3 Download**: Downloads the binary file.
4.  **HTTP Request**: POSTs the file to the local API endpoint `http://localhost:5000/api/evidence/upload`.
5.  **Email**: Notifies the judge.
