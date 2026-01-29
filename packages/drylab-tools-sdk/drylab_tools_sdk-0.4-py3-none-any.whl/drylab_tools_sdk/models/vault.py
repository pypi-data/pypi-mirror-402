"""Vault data models."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class VaultFile:
    """Represents a file in the vault."""

    filename: str
    size: Optional[int] = None
    created_at: Optional[str] = None

    def __repr__(self) -> str:
        size_str = f"{self.size} bytes" if self.size else "unknown size"
        return f"{self.filename} ({size_str})"


@dataclass
class VaultFolder:
    """Represents a folder in the vault."""

    folder_name: str

    def __repr__(self) -> str:
        return f"{self.folder_name}/"


@dataclass
class UploadResult:
    """Result of an upload operation."""

    vault_path: str
    success: bool
    status: str

    def __repr__(self) -> str:
        if self.success:
            return f"✓ {self.status}\n  Path: {self.vault_path}"
        else:
            return f"✗ {self.status}"


@dataclass
class DownloadResult:
    """Result of a download operation."""

    local_path: str
    vault_path: str
    success: bool
    status: str

    def __repr__(self) -> str:
        if self.success:
            return f"✓ {self.status}\n  From: {self.vault_path}\n  To: {self.local_path}"
        else:
            return f"✗ {self.status}"


@dataclass
class ListFilesResult:
    """Result of listing files in a folder."""

    vault_path: str
    files: List[VaultFile] = field(default_factory=list)
    subfolders: List[VaultFolder] = field(default_factory=list)
    success: bool = True
    status: str = "Listed successfully."

    def __repr__(self) -> str:
        if not self.success:
            return f"✗ {self.status}"
        
        lines = [f"✓ {self.status}", f"{self.vault_path}/"]
        
        # Combine subfolders and files for tree display
        all_items = [(True, sf.folder_name) for sf in self.subfolders] + \
                    [(False, f.filename) for f in self.files]
        
        for i, (is_folder, name) in enumerate(all_items):
            is_last = (i == len(all_items) - 1)
            prefix = "`-- " if is_last else "|-- "
            suffix = "/" if is_folder else ""
            lines.append(f"{prefix}{name}{suffix}")
        
        if not all_items:
            lines.append("    (empty)")
        
        return "\n".join(lines)
