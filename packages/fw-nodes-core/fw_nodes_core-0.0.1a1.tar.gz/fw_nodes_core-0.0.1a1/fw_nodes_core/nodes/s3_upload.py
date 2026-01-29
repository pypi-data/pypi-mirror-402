"""Upload files to S3-compatible storage."""

from typing import Any, ClassVar, Optional

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from pydantic import BaseModel, Field


class S3CredentialSchema(BaseModel):
    """Credential schema for S3-compatible storage."""

    # Class-level display metadata (optional)
    credential_name: ClassVar[str] = "S3 Storage"
    credential_description: ClassVar[str] = "AWS S3 or S3-compatible storage credentials"
    credential_icon: ClassVar[Optional[str]] = "☁️"

    # Instance fields (actual credential data)
    endpoint_url: Optional[str] = Field(None, description="Custom S3 endpoint URL (e.g., 'https://nyc3.digitaloceanspaces.com')")
    access_key: str = Field(..., description="AWS access key ID")
    secret_key: str = Field(..., description="AWS secret access key")
    region: str = Field(default="us-east-1", description="AWS region")


class S3UploadInput(BaseModel):
    credential_id: str = Field(..., description="S3 credential to use")
    file_content: str = Field("", description="File content to upload. Use Insert button to reference data from other nodes.")
    bucket: str = Field(..., description="S3 bucket name. Use Insert button to reference project variables or metadata (e.g., {{_meta.execution_id}}).")
    key: str = Field(..., description="S3 object key (file path). Use Insert button to reference metadata (e.g., data/{{_meta.execution_id}}/output.jsonl).")
    content_type: Optional[str] = Field(default="application/octet-stream", description="Content-Type header for the uploaded file")


class S3UploadOutput(BaseNodeOutput):
    uri: str = Field(..., description="S3 URI of the uploaded file (s3://bucket/key)")
    bucket: str = Field(..., description="Bucket name")
    key: str = Field(..., description="Object key")
    size_bytes: int = Field(..., description="Size of the uploaded file in bytes")
    uploaded: bool = Field(..., description="Whether upload was successful")


class S3UploadNode(BaseNode):
    """Upload file content to S3 or S3-compatible storage."""

    input_schema = S3UploadInput
    output_schema = S3UploadOutput
    credential_schema = S3CredentialSchema

    metadata = NodeMetadata(
        name="S3 Upload",
        description="Upload files to AWS S3 or S3-compatible storage (MinIO, DigitalOcean Spaces, etc.)",
        category="s3",
        icon="☁️",
        color="#FF6F00",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Upload file content to S3."""
        import boto3
        from botocore.exceptions import ClientError

        # Resolve credential
        credential_data = await context.resolve_credential(
            credential_id=validated_inputs["credential_id"],
            credential_type=self.get_credential_type()
        )

        file_content = validated_inputs.get("file_content")
        if not file_content:
            raise ValueError("File content is required. Provide 'file_content' field or connect from a previous node.")

        bucket = validated_inputs.get("bucket")
        key = validated_inputs.get("key")
        content_type = validated_inputs.get("content_type", "application/x-ndjson")

        # Extract credentials
        access_key = credential_data["access_key"]
        secret_key = credential_data["secret_key"]
        region = credential_data.get("region", "us-east-1")
        endpoint_url = credential_data.get("endpoint_url")

        # Convert content to bytes if it's a string
        if isinstance(file_content, str):
            file_bytes = file_content.encode("utf-8")
        elif isinstance(file_content, bytes):
            file_bytes = file_content
        else:
            # Try to serialize as JSON if it's an object
            import json
            try:
                file_bytes = json.dumps(file_content, ensure_ascii=False).encode("utf-8")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Cannot convert file_content to bytes: {e}") from e

        # Create S3 client
        from botocore.config import Config

        s3_client_kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
        }

        # For S3-compatible storage, use path-style addressing
        if endpoint_url:
            s3_client_kwargs["endpoint_url"] = endpoint_url
            s3_client_kwargs["config"] = Config(
                s3={"addressing_style": "path"},
                signature_version="s3v4",
            )

        try:
            s3_client = boto3.client("s3", **s3_client_kwargs)

            # Upload file
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )

            # Build S3 URI
            s3_uri = f"s3://{bucket}/{key}"

            # Return Pydantic instance (flat output)
            return S3UploadOutput(
                uri=s3_uri,
                bucket=bucket,
                key=key,
                size_bytes=len(file_bytes),
                uploaded=True,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            raise ValueError(f"S3 upload failed ({error_code}): {error_message}") from e
        except Exception as e:
            raise ValueError(f"S3 upload failed: {str(e)}") from e
