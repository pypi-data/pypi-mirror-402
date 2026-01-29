"""Vault file operations."""

import os
from typing import Optional

import requests

from drylab_tools_sdk.resources.base import BaseResource
from drylab_tools_sdk.models.vault import (
    VaultFile,
    VaultFolder,
    UploadResult,
    DownloadResult,
    ListFilesResult,
)


class VaultResource(BaseResource):
    """
    Vault file storage operations.

    Provides methods to upload, download, and list files in the Drylab vault.
    Files are organized in a hierarchical structure: /ProjectName/Folder/SubFolder/file.txt

    Example:
        # List files in a folder
        result = client.vault.list("/MyProject/data")
        if result.success:
            print(result)

        # Upload a file
        result = client.vault.upload("/MyProject/output", "/tmp/result.csv")
        print(result)  # Shows success or error message
    """

    def list(self, vault_path: str) -> ListFilesResult:
        """
        List files and subfolders at the given path.

        Args:
            vault_path: Path to folder, e.g., "/ProjectName/Folder"

        Returns:
            ListFilesResult with files and subfolders

        Example:
            result = client.vault.list("/MyProject/data")
            print(result)
        """
        try:
            response = self._http.post("/api/v1/ai/vault/files/list", json={"vault_path": vault_path})
            
            files = [
                VaultFile(
                    filename=f["filename"],
                    size=f.get("file_size"),
                    created_at=f.get("created_at"),
                )
                for f in response.get("files", [])
            ]
            
            subfolders = [
                VaultFolder(folder_name=f["folder_name"])
                for f in response.get("subfolders", [])
            ]
            
            file_count = len(files)
            folder_count = len(subfolders)
            
            if file_count == 0 and folder_count == 0:
                status_msg = f"Listed successfully. Folder is empty."
            else:
                status_msg = f"Listed successfully. Found {file_count} file(s) and {folder_count} folder(s)."
            
            return ListFilesResult(
                vault_path=response["vault_path"],
                files=files,
                subfolders=subfolders,
                success=True,
                status=status_msg,
            )
            
        except requests.exceptions.ConnectionError:
            return ListFilesResult(
                vault_path=vault_path,
                files=[],
                subfolders=[],
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return ListFilesResult(
                    vault_path=vault_path,
                    files=[],
                    subfolders=[],
                    success=False,
                    status=f"Folder not found: {vault_path}. Please check the path is correct.",
                )
            elif e.response.status_code == 403:
                return ListFilesResult(
                    vault_path=vault_path,
                    files=[],
                    subfolders=[],
                    success=False,
                    status=f"Access denied to folder: {vault_path}. You may not have permission to access this location.",
                )
            else:
                return ListFilesResult(
                    vault_path=vault_path,
                    files=[],
                    subfolders=[],
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return ListFilesResult(
                vault_path=vault_path,
                files=[],
                subfolders=[],
                success=False,
                status=f"Unexpected error while listing files: {str(e)}. Please report this to the Drylab team.",
            )

    def upload(
        self,
        vault_path: str,
        local_path: str,
        filename: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload a local file to the vault.

        Folders in the path will be created automatically if they don't exist.

        Args:
            vault_path: Destination folder path, e.g., "/ProjectName/output"
            local_path: Path to the local file to upload
            filename: Optional name for the uploaded file (defaults to local filename)

        Returns:
            UploadResult with vault_path and status

        Example:
            result = client.vault.upload(
                vault_path="/MyProject/output",
                local_path="/tmp/analysis_result.csv"
            )
            print(result)
        """
        # Pre-validation: Check local file exists
        if not os.path.exists(local_path):
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status=f"Local file not found: {local_path}. Please check the file path exists.",
            )
        
        if not os.path.isfile(local_path):
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status=f"Path is not a file: {local_path}. Please provide a file path, not a directory.",
            )
        
        if filename is None:
            filename = os.path.basename(local_path)

        try:
            file_size = os.path.getsize(local_path)
        except OSError as e:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status=f"Cannot read file size: {str(e)}. Please check file permissions.",
            )

        # Get presigned URL from backend
        try:
            response = self._http.post(
                "/api/v1/ai/vault/files/presigned-url",
                json={
                    "vault_path": vault_path,
                    "filename": filename,
                    "file_size": file_size,
                },
            )
        except requests.exceptions.ConnectionError:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return UploadResult(
                    vault_path=vault_path,
                    success=False,
                    status=f"Destination folder not found: {vault_path}. Please check the path is correct.",
                )
            elif e.response.status_code == 403:
                return UploadResult(
                    vault_path=vault_path,
                    success=False,
                    status=f"Access denied to folder: {vault_path}. You may not have permission to upload to this location.",
                )
            elif e.response.status_code == 409:
                return UploadResult(
                    vault_path=vault_path,
                    success=False,
                    status=f"A file with name '{filename}' already exists in {vault_path}. Please use a different filename or delete the existing file first.",
                )
            else:
                return UploadResult(
                    vault_path=vault_path,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status=f"Error getting upload URL: {str(e)}. Please try again later.",
            )

        # Upload the file to S3
        try:
            presigned_url = response["presigned_url"]
            result_vault_path = response["vault_path"]
            
            with open(local_path, "rb") as f:
                upload_response = requests.put(
                    presigned_url,
                    data=f,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=300,  # 5 minute timeout for large files
                )
            
            if upload_response.status_code not in (200, 201):
                return UploadResult(
                    vault_path=vault_path,
                    success=False,
                    status=f"Upload to S3 failed (HTTP {upload_response.status_code}). This may be due to network issues or S3 service problems. Please try again later.",
                )
            
            return UploadResult(
                vault_path=result_vault_path,
                success=True,
                status=f"File uploaded successfully to {result_vault_path}.",
            )
            
        except requests.exceptions.Timeout:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status="Upload timed out. The file may be too large or the network connection is slow. Please try again with a smaller file or check your network connection.",
            )
        except requests.exceptions.ConnectionError:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status="Network connection lost during upload. Please check your internet connection and try again.",
            )
        except IOError as e:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status=f"Cannot read local file: {str(e)}. Please check file permissions.",
            )
        except Exception as e:
            return UploadResult(
                vault_path=vault_path,
                success=False,
                status=f"Unexpected error during upload: {str(e)}. Please report this to the Drylab team.",
            )
        
    def download(
        self,
        local_path: str,
        vault_path: str,
    ) -> DownloadResult:
        """
        Download a file from the vault to local filesystem.

        Args:
            local_path: Where to save the file locally
            vault_path: Full path to file in vault, e.g., "/ProjectName/data/file.txt"

        Returns:
            DownloadResult with local_path, vault_path, and status

        Example:
            result = client.vault.download(
                local_path="/tmp/input.fastq",
                vault_path="/MyProject/data/input.fastq"
            )
            print(result)
        """
        # Pre-validation: Check if local directory exists and is writable
        local_dir = os.path.dirname(local_path) or "."
        if not os.path.exists(local_dir):
            try:
                os.makedirs(local_dir, exist_ok=True)
            except OSError as e:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"Cannot create directory {local_dir}: {str(e)}. Please check permissions.",
                )
        
        if os.path.exists(local_path) and not os.access(local_path, os.W_OK):
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Cannot write to {local_path}. Please check file permissions.",
            )

        # Get presigned download URL from backend
        try:
            response = self._http.post(
                "/api/v1/ai/vault/files/download-url",
                json={
                    "vault_path": vault_path,
                    "file_id": None,
                },
            )
        except requests.exceptions.ConnectionError:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"File not found: {vault_path}. Please check the path is correct.",
                )
            elif e.response.status_code == 403:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"Access denied to file: {vault_path}. You may not have permission to download this file.",
                )
            else:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Error getting download URL: {str(e)}. Please try again later.",
            )

        download_url = response["download_url"]

        # Download the file from S3
        try:
            download_response = requests.get(download_url, stream=True, timeout=300)
            download_response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=True,
                status=f"File downloaded successfully to {local_path}.",
            )
            
        except requests.exceptions.Timeout:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status="Download timed out. The file may be too large or the network connection is slow. Please try again.",
            )
        except requests.exceptions.ConnectionError:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status="Network connection lost during download. Please check your internet connection and try again.",
            )
        except IOError as e:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Cannot write to {local_path}: {str(e)}. Please check file permissions.",
            )
        except Exception as e:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Unexpected error during download: {str(e)}. Please report this to the Drylab team.",
            )

    def download_folder(
        self,
        local_path: str,
        vault_path: str,
    ) -> DownloadResult:
        """
        Download a folder as a zip file.

        Args:
            local_path: Where to save the zip file locally
            vault_path: Path to folder in vault, e.g., "/ProjectName/results"

        Returns:
            DownloadResult with local_path, vault_path, and status

        Example:
            result = client.vault.download_folder(
                local_path="/tmp/results.zip",
                vault_path="/MyProject/results"
            )
            print(result)
        """
        # Pre-validation: Check if local directory exists and is writable
        local_dir = os.path.dirname(local_path) or "."
        if not os.path.exists(local_dir):
            try:
                os.makedirs(local_dir, exist_ok=True)
            except OSError as e:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"Cannot create directory {local_dir}: {str(e)}. Please check permissions.",
                )
        
        if os.path.exists(local_path) and not os.access(local_path, os.W_OK):
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Cannot write to {local_path}. Please check file permissions.",
            )

        # Get presigned download URL from backend
        try:
            response = self._http.post(
                "/api/v1/ai/vault/folders/download-zip",
                json={
                    "vault_path": vault_path,
                    "folder_id": None,
                },
            )
        except requests.exceptions.ConnectionError:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"Folder not found: {vault_path}. Please check the path is correct.",
                )
            elif e.response.status_code == 403:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"Access denied to folder: {vault_path}. You may not have permission to download this folder.",
                )
            else:
                return DownloadResult(
                    local_path=local_path,
                    vault_path=vault_path,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Error getting download URL: {str(e)}. Please try again later.",
            )

        download_url = response["download_url"]
        file_count = response.get("file_count", 0)

        if file_count == 0:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Folder is empty: {vault_path}. Nothing to download.",
            )

        # Download the zip from S3
        try:
            download_response = requests.get(download_url, stream=True, timeout=600)  # 10 min timeout for large folders
            download_response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=True,
                status=f"Downloaded {file_count} file(s) to {local_path}.",
            )
            
        except requests.exceptions.Timeout:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status="Download timed out. The folder may be too large or the network connection is slow. Please try again.",
            )
        except requests.exceptions.ConnectionError:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status="Network connection lost during download. Please check your internet connection and try again.",
            )
        except IOError as e:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Cannot write to {local_path}: {str(e)}. Please check file permissions.",
            )
        except Exception as e:
            return DownloadResult(
                local_path=local_path,
                vault_path=vault_path,
                success=False,
                status=f"Unexpected error during download: {str(e)}. Please report this to the Drylab team.",
            )
