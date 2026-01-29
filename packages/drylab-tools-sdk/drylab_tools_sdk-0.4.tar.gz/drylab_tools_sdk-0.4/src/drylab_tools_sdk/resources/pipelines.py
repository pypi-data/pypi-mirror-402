"""Pipeline registry operations."""

from typing import Optional, List, Dict, Any

import requests

from drylab_tools_sdk.resources.base import BaseResource
from drylab_tools_sdk.models.pipeline import (
    Pipeline,
    PipelineSchema,
    PipelineListResult,
    PipelineDeleteResult,
    SchemaField,
)


class PipelinesResource(BaseResource):
    """
    Pipeline registry operations.

    List available pipelines, get parameter schemas, and register custom pipelines.

    Example:
        # List available pipelines
        result = client.pipelines.list()
        if result.success:
            for p in result.pipelines:
                print(f"{p.name}: {p.description}")

        # Get pipeline schema
        schema = client.pipelines.get("rnaseq")
        if schema.success:
            print(schema)
    """

    def list(self) -> PipelineListResult:
        """
        List all available pipelines (both public and user-uploaded).

        Returns:
            PipelineListResult with pipelines list and status

        Example:
            result = client.pipelines.list()
            print(result)
        """
        try:
            response = self._http.post(
                "/api/v1/ai/nextflow/pipelines/list",
                json={
                    "include_public": True,
                    "include_user": True,
                    "project_id": None,
                },
            )

            pipelines = [Pipeline.from_response(p) for p in response]
            
            return PipelineListResult(
                pipelines=pipelines,
                success=True,
                status=f"Found {len(pipelines)} pipeline(s).",
            )
            
        except requests.exceptions.ConnectionError:
            return PipelineListResult(
                pipelines=[],
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            return PipelineListResult(
                pipelines=[],
                success=False,
                status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
            )
        except Exception as e:
            return PipelineListResult(
                pipelines=[],
                success=False,
                status=f"Unexpected error while listing pipelines: {str(e)}. Please report this to the Drylab team.",
            )

    def get(
        self,
        pipeline_id: str,
        version: Optional[str] = None,
    ) -> PipelineSchema:
        """
        Get the parameter schema for a pipeline.

        The schema describes all available parameters, their types,
        whether they're required, and which ones are file paths.

        Args:
            pipeline_id: Pipeline ID (e.g., "rnaseq" or "user-{uuid}")
            version: Pipeline version (optional, defaults to latest)

        Returns:
            PipelineSchema with field definitions

        Example:
            schema = client.pipelines.get("rnaseq")
            if schema.success:
                print(f"Path fields: {schema.path_fields}")
        """
        try:
            response = self._http.post(
                f"/api/v1/ai/nextflow/pipelines/{pipeline_id}/schema",
                json={"version": version},
            )

            return PipelineSchema(
                pipeline_id=response.get("pipeline_id", pipeline_id),
                fields=[
                    SchemaField(
                        name=f["name"],
                        type=f["type"],
                        is_path=f.get("is_path", False),
                        required=f.get("required", False),
                        description=f.get("description", ""),
                        default=f.get("default"),
                    )
                    for f in response.get("fields", [])
                ],
                path_fields=response.get("path_fields", []),
                success=True,
                status=f"Retrieved schema for pipeline '{pipeline_id}'.",
            )
            
        except requests.exceptions.ConnectionError:
            return PipelineSchema(
                pipeline_id=pipeline_id,
                fields=[],
                path_fields=[],
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return PipelineSchema(
                    pipeline_id=pipeline_id,
                    fields=[],
                    path_fields=[],
                    success=False,
                    status=f"Pipeline not found: {pipeline_id}. Please check the pipeline ID is correct.",
                )
            else:
                return PipelineSchema(
                    pipeline_id=pipeline_id,
                    fields=[],
                    path_fields=[],
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return PipelineSchema(
                pipeline_id=pipeline_id,
                fields=[],
                path_fields=[],
                success=False,
                status=f"Unexpected error while retrieving schema: {str(e)}. Please report this to the Drylab team.",
            )

    def register(
        self,
        name: str,
        pipeline_zip_path: str,
        schema: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Pipeline:
        """
        Register a custom Nextflow pipeline.

        The pipeline zip should contain:
        - main.nf: Main Nextflow script
        - nextflow.config: Pipeline configuration with params

        Args:
            name: Name for the pipeline
            pipeline_zip_path: Vault path to pipeline zip (e.g., "/ProjectName/pipelines/my-pipeline.zip")
            schema: Parameter schema - minimal format with just path_fields
            description: Pipeline description (optional)

        Returns:
            Registered Pipeline object

        Example:
            pipeline = client.pipelines.register(
                name="my-custom-analysis",
                pipeline_zip_path="/MyProject/pipelines/analysis.zip",
                schema={
                    "path_fields": ["input_file", "outdir", "reference"]
                },
                description="Custom analysis pipeline"
            )
            if pipeline.success:
                print(f"Registered: {pipeline.id}")
        """
        # Pre-validation: Check schema format
        if not isinstance(schema, dict):
            return Pipeline(
                id="",
                name=name,
                success=False,
                status="Invalid schema format. Schema must be a dictionary/JSON object.",
            )
        
        if "path_fields" not in schema:
            return Pipeline(
                id="",
                name=name,
                success=False,
                status="Schema must include 'path_fields' array. Example: {'path_fields': ['input_file', 'outdir']}",
            )
        
        if not isinstance(schema.get("path_fields"), list):
            return Pipeline(
                id="",
                name=name,
                success=False,
                status="'path_fields' must be a list/array. Example: {'path_fields': ['input_file', 'outdir']}",
            )

        try:
            response = self._http.post(
                "/api/v1/ai/nextflow/pipelines/register",
                json={
                    "pipeline_name": name,
                    "pipeline_zip_vault_path": pipeline_zip_path,
                    "schema_json": schema,
                    "description": description,
                    "project_id": None,
                },
            )

            return Pipeline.from_response(
                response,
                success=True,
                status=f"Pipeline '{name}' registered successfully with ID: {response.get('id', 'unknown')}.",
            )
            
        except requests.exceptions.ConnectionError:
            return Pipeline(
                id="",
                name=name,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return Pipeline(
                    id="",
                    name=name,
                    success=False,
                    status=f"Pipeline zip file not found: {pipeline_zip_path}. Please check the vault path is correct.",
                )
            elif e.response.status_code == 400:
                # Try to extract error message from response
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    if "zip" in error_detail.lower() or "main.nf" in error_detail.lower():
                        return Pipeline(
                            id="",
                            name=name,
                            success=False,
                            status=f"Invalid pipeline zip: {error_detail}. The zip must contain 'main.nf' and optionally 'nextflow.config'.",
                        )
                    elif "schema" in error_detail.lower():
                        return Pipeline(
                            id="",
                            name=name,
                            success=False,
                            status=f"Invalid schema: {error_detail}. Please check the schema format.",
                        )
                    else:
                        return Pipeline(
                            id="",
                            name=name,
                            success=False,
                            status=f"Validation error: {error_detail}",
                        )
                except:
                    return Pipeline(
                        id="",
                        name=name,
                        success=False,
                        status=f"Validation error (HTTP 400). Please check the pipeline zip and schema format.",
                    )
            else:
                return Pipeline(
                    id="",
                    name=name,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return Pipeline(
                id="",
                name=name,
                success=False,
                status=f"Unexpected error while registering pipeline: {str(e)}. Please report this to the Drylab team.",
            )

    def delete(self, pipeline_id: str) -> PipelineDeleteResult:
        """
        Delete a user-uploaded pipeline.

        Only user pipelines (prefixed with "user-") can be deleted.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            PipelineDeleteResult with success status

        Example:
            result = client.pipelines.delete("user-550e8400-e29b-41d4-a716-446655440000")
            print(result)
        """
        # Pre-validation: Check if it's a user pipeline
        if not pipeline_id.startswith("user-"):
            return PipelineDeleteResult(
                pipeline_id=pipeline_id,
                success=False,
                status="Cannot delete public pipelines. Only user-uploaded pipelines (prefixed with 'user-') can be deleted.",
            )

        try:
            self._http.post(
                f"/api/v1/ai/nextflow/pipelines/{pipeline_id}/delete",
                json={},
            )
            
            return PipelineDeleteResult(
                pipeline_id=pipeline_id,
                success=True,
                status=f"Pipeline '{pipeline_id}' deleted successfully.",
            )
            
        except requests.exceptions.ConnectionError:
            return PipelineDeleteResult(
                pipeline_id=pipeline_id,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return PipelineDeleteResult(
                    pipeline_id=pipeline_id,
                    success=False,
                    status=f"Pipeline not found: {pipeline_id}. It may have already been deleted.",
                )
            elif e.response.status_code == 400:
                return PipelineDeleteResult(
                    pipeline_id=pipeline_id,
                    success=False,
                    status="Cannot delete public pipelines. Only user-uploaded pipelines can be deleted.",
                )
            else:
                return PipelineDeleteResult(
                    pipeline_id=pipeline_id,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return PipelineDeleteResult(
                pipeline_id=pipeline_id,
                success=False,
                status=f"Unexpected error while deleting pipeline: {str(e)}. Please report this to the Drylab team.",
            )
