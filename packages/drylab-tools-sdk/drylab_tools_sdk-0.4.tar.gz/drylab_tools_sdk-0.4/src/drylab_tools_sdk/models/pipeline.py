"""Pipeline data models."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SchemaField:
    """A field in a pipeline parameter schema."""

    name: str
    type: str
    is_path: bool = False
    required: bool = False
    description: str = ""
    default: Any = None

    def __repr__(self) -> str:
        req = " (required)" if self.required else ""
        path = " [path]" if self.is_path else ""
        return f"{self.name}: {self.type}{req}{path}"


@dataclass
class PipelineSchema:
    """Parameter schema for a pipeline."""

    pipeline_id: str
    fields: List[SchemaField] = field(default_factory=list)
    path_fields: List[str] = field(default_factory=list)
    success: bool = True
    status: str = "Schema retrieved successfully."

    @property
    def required_fields(self) -> List[SchemaField]:
        """Get required fields."""
        return [f for f in self.fields if f.required]

    @property
    def optional_fields(self) -> List[SchemaField]:
        """Get optional fields."""
        return [f for f in self.fields if not f.required]

    def __repr__(self) -> str:
        if not self.success:
            return f"✗ {self.status}"
        
        lines = [f"✓ {self.status}"]
        lines.append(f"Pipeline: {self.pipeline_id}")
        lines.append(f"Path fields: {self.path_fields}")
        
        if self.fields:
            lines.append("Parameters:")
            for f in self.fields:
                lines.append(f"  - {f}")
        
        return "\n".join(lines)


@dataclass
class Pipeline:
    """Represents a Nextflow pipeline."""

    id: str
    name: str
    description: str = ""
    source: str = "registry"  # "registry" or "user-upload"
    path: str = ""
    default_version: str = "main"
    success: bool = True
    status: str = "Pipeline retrieved successfully."

    @classmethod
    def from_response(cls, data: Dict[str, Any], success: bool = True, status: str = "Pipeline retrieved successfully.") -> "Pipeline":
        """Create Pipeline from API response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", data.get("pipeline_name", "")),
            description=data.get("description", ""),
            source=data.get("source", "registry"),
            path=data.get("path", data.get("pipeline_zip_s3_path", "")),
            default_version=data.get("default_version", "main"),
            success=success,
            status=status,
        )

    def __repr__(self) -> str:
        if not self.success:
            return f"✗ {self.status}"
        return f"✓ {self.status}\n  ID: {self.id}\n  Name: {self.name}"


@dataclass
class PipelineListResult:
    """Result of listing pipelines."""

    pipelines: List[Pipeline] = field(default_factory=list)
    success: bool = True
    status: str = "Pipelines listed successfully."

    def __repr__(self) -> str:
        if not self.success:
            return f"✗ {self.status}"
        
        lines = [f"✓ {self.status}"]
        lines.append(f"Found {len(self.pipelines)} pipelines:")
        for p in self.pipelines:
            source_tag = "[user]" if p.source == "user-upload" else "[public]"
            lines.append(f"  - {p.id}: {p.name} {source_tag}")
        return "\n".join(lines)


@dataclass
class PipelineDeleteResult:
    """Result of deleting a pipeline."""

    pipeline_id: str
    success: bool
    status: str

    def __repr__(self) -> str:
        if self.success:
            return f"✓ {self.status}"
        else:
            return f"✗ {self.status}"
