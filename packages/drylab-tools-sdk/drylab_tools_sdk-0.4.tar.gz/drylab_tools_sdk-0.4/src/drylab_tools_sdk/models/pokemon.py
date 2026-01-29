"""
Pokemon tool models for SDK.

Defines dataclasses for tool information and job results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PokemonTool:
    """A Pokemon protein structure prediction tool."""
    id: str
    name: str
    description: str
    compute_credit: float

    def __repr__(self) -> str:
        return f"{self.name} ({self.id}) - {self.compute_credit} credits"


@dataclass
class ToolSearchResult:
    """Result from tool search."""
    tools: List[PokemonTool]
    query: str
    success: bool = True
    status: str = "Search completed."

    def __repr__(self) -> str:
        if self.success:
            if not self.tools:
                return f"✓ No tools found matching '{self.query}'."
            lines = [f"✓ Found {len(self.tools)} tool(s) for '{self.query}':"]
            for t in self.tools:
                lines.append(f"  - {t.id}: {t.description} ({t.compute_credit} credits)")
            return "\n".join(lines)
        return f"✗ {self.status}"


@dataclass
class PokemonJobResult:
    """Result from a Pokemon job execution."""
    tool_id: str
    vault_path: str
    output_files: List[str] = field(default_factory=list)
    execution_time_ms: Optional[int] = None
    success: bool = True
    status: str = "Job completed successfully."

    @property
    def is_success(self) -> bool:
        """Check if job completed successfully."""
        return self.success

    def __repr__(self) -> str:
        if self.success:
            lines = [f"✓ {self.status}"]
            lines.append(f"  Tool: {self.tool_id}")
            lines.append(f"  Results: {self.vault_path}")
            if self.execution_time_ms:
                lines.append(f"  Time: {self.execution_time_ms}ms")
            if self.output_files:
                lines.append(f"  Files: {len(self.output_files)} output file(s)")
                for f in self.output_files[:5]:
                    lines.append(f"    - {f}")
                if len(self.output_files) > 5:
                    lines.append(f"    ... and {len(self.output_files) - 5} more")
            return "\n".join(lines)
        return f"✗ {self.status}"
