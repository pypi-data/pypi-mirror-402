"""OneDrive Client implementation using Microsoft Graph API."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import quote
import requests


class OneDriveClient:
    """Client for interacting with Microsoft OneDrive via Graph API.
    
    This client uses the Microsoft Graph API to perform operations on OneDrive.
    Authentication is handled via access tokens that should be provided through
    environment variables or secure secret management systems.
    
    Required environment variables:
        ONEDRIVE_ACCESS_TOKEN: OAuth2 access token for Microsoft Graph API
    
    Optional environment variables:
        ONEDRIVE_API_BASE_URL: Base URL for Microsoft Graph API 
                               (default: https://graph.microsoft.com/v1.0)
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize OneDrive client.
        
        Args:
            access_token: OAuth2 access token. If not provided, will attempt
                         to read from ONEDRIVE_ACCESS_TOKEN environment variable.
        
        Raises:
            ValueError: If no access token is provided or found in environment.
        """
        self.access_token = access_token or os.getenv("ONEDRIVE_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "No access token provided. Either pass access_token parameter "
                "or set ONEDRIVE_ACCESS_TOKEN environment variable."
            )
        
        self.api_base_url = os.getenv(
            "ONEDRIVE_API_BASE_URL", 
            "https://graph.microsoft.com/v1.0"
        )
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str,
        return_json: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """Make an HTTP request to the Microsoft Graph API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            return_json: If True, parse and return JSON response. If False, return raw response
            custom_headers: Optional custom headers to merge with default headers
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            JSON response from the API (if return_json=True) or requests.Response object
        
        Raises:
            requests.exceptions.HTTPError: If the request fails
        """
        url = f"{self.api_base_url}{endpoint}"
        headers = self.headers.copy()
        if custom_headers:
            headers.update(custom_headers)
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()
        
        if not return_json:
            return response
        
        # Some responses (like DELETE) may not have content
        if response.status_code == 204 or not response.content:
            return {}
        
        return response.json()
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user.
        
        Returns:
            Dictionary containing user information
        """
        return self._make_request("GET", "/me")
    
    def list_root_items(self) -> List[Dict[str, Any]]:
        """List items in the root of the user's OneDrive.
        
        Returns:
            List of items (files and folders) in the root directory
        """
        response = self._make_request("GET", "/me/drive/root/children")
        return response.get("value", [])
    
    def list_items(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """List items in a specific folder.
        
        Args:
            folder_path: Path to the folder (e.g., "Documents/MyFolder")
                        If empty, lists root items.
        
        Returns:
            List of items in the specified folder
        """
        if not folder_path:
            return self.list_root_items()
        
        # URL-encode the folder path, preserving forward slashes for path separators
        encoded_path = quote(folder_path, safe='/')
        endpoint = f"/me/drive/root:/{encoded_path}:/children"
        response = self._make_request("GET", endpoint)
        return response.get("value", [])
    
    def get_item_info(self, item_id: str) -> Dict[str, Any]:
        """Get information about a specific item.
        
        Args:
            item_id: The ID of the item
        
        Returns:
            Dictionary containing item information
        """
        return self._make_request("GET", f"/me/drive/items/{item_id}")
    
    def download_file(self, item_id: str) -> bytes:
        """Download a file from OneDrive.
        
        Args:
            item_id: The ID of the file to download
        
        Returns:
            File content as bytes
        """
        endpoint = f"/me/drive/items/{item_id}/content"
        response = self._make_request("GET", endpoint, return_json=False)
        return response.content
    
    def upload_file(
        self, 
        file_path: str, 
        content: bytes
    ) -> Dict[str, Any]:
        """Upload a file to OneDrive.
        
        Note: This method will overwrite any existing file at the specified path.
        This is the default behavior of the Microsoft Graph API PUT endpoint.
        
        Args:
            file_path: Path where to upload the file (e.g., "Documents/myfile.txt")
            content: File content as bytes
        
        Returns:
            Dictionary containing information about the uploaded file
        """
        # URL-encode the file path, preserving forward slashes for path separators
        encoded_path = quote(file_path, safe='/')
        endpoint = f"/me/drive/root:/{encoded_path}:/content"
        custom_headers = {"Content-Type": "application/octet-stream"}
        return self._make_request(
            "PUT", 
            endpoint, 
            custom_headers=custom_headers,
            data=content
        )
    
    def create_folder(
        self, 
        folder_name: str, 
        parent_path: str = "",
        conflict_behavior: str = "rename"
    ) -> Dict[str, Any]:
        """Create a new folder in OneDrive.
        
        Args:
            folder_name: Name of the folder to create
            parent_path: Path to parent folder (empty for root)
            conflict_behavior: How to handle naming conflicts. Options:
                              - "rename": Automatically rename if folder exists (default)
                              - "replace": Replace existing folder
                              - "fail": Return error if folder exists
        
        Returns:
            Dictionary containing information about the created folder
        """
        if parent_path:
            # URL-encode the parent path, preserving forward slashes for path separators
            encoded_path = quote(parent_path, safe='/')
            endpoint = f"/me/drive/root:/{encoded_path}:/children"
        else:
            endpoint = "/me/drive/root/children"
        
        data = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": conflict_behavior
        }
        
        return self._make_request("POST", endpoint, json=data)
    
    def delete_item(self, item_id: str) -> None:
        """Delete an item from OneDrive.
        
        Args:
            item_id: The ID of the item to delete
        """
        self._make_request("DELETE", f"/me/drive/items/{item_id}")
    
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        """Search for items in OneDrive.
        
        Args:
            query: Search query string
        
        Returns:
            List of items matching the search query
        """
        # URL-encode the query, preserving spaces for search functionality
        # Note: Microsoft Graph API handles spaces in search queries
        encoded_query = quote(query, safe=' ')
        endpoint = f"/me/drive/root/search(q='{encoded_query}')"
        response = self._make_request("GET", endpoint)
        return response.get("value", [])


class OneDriveSkill:
    """Skill wrapper for OneDrive operations.
    
    This class provides a simplified interface for common OneDrive operations
    that can be easily integrated with LLM systems. It includes safety features
    such as user confirmation for destructive operations.
    
    Attributes:
        client: OneDriveClient instance for API operations
        confirmation_callback: Optional callback function for user confirmations
    """
    
    def __init__(
        self, 
        access_token: Optional[str] = None,
        confirmation_callback: Optional[Callable[[str], bool]] = None
    ):
        """Initialize OneDrive skill.
        
        Args:
            access_token: OAuth2 access token. If not provided, will attempt
                         to read from ONEDRIVE_ACCESS_TOKEN environment variable.
            confirmation_callback: Optional function that takes a confirmation message
                                  and returns True if user confirms, False otherwise.
                                  If not provided, uses default console input.
        """
        self.client = OneDriveClient(access_token=access_token)
        self.confirmation_callback = confirmation_callback or self._default_confirmation
    
    def _default_confirmation(self, message: str) -> bool:
        """Default confirmation handler using console input.
        
        Args:
            message: Confirmation message to display
            
        Returns:
            True if user confirms, False otherwise
        """
        print(f"\n⚠️  CONFIRMATION REQUIRED ⚠️")
        print(f"{message}")
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    def get_skill_metadata(self) -> Dict[str, Any]:
        """Get skill metadata for LLM discovery.
        
        Returns:
            Dictionary containing skill metadata including available operations,
            parameters, safety levels, and descriptions.
        """
        # Try to load from skill_manifest.json using pathlib
        try:
            manifest_path = Path(__file__).parent.parent / 'skill_manifest.json'
            
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            # If file doesn't exist or can't be parsed, fall through to default
            pass
        
        # Fallback to inline metadata
        return {
            "name": "onedrive-connect",
            "version": "0.1.0",
            "description": "A skill for connecting to Microsoft OneDrive",
            "skills": [
                {"name": "list_files", "safety": "read-only"},
                {"name": "search", "safety": "read-only"},
                {"name": "get_file_content", "safety": "read-only"},
                {"name": "upload_content", "safety": "write", "requires_confirmation": True},
                {"name": "create_folder", "safety": "write"},
                {"name": "delete_item", "safety": "destructive", "requires_confirmation": True}
            ]
        }
    
    def list_files(self, folder_path: str = "") -> str:
        """List files in a folder (skill-friendly output).
        
        Args:
            folder_path: Path to the folder (empty for root)
        
        Returns:
            Formatted string with file listing
        """
        items = self.client.list_items(folder_path)
        if not items:
            return "No items found in the specified folder."
        
        result = []
        for item in items:
            item_type = "Folder" if "folder" in item else "File"
            name = item.get("name", "Unknown")
            size = item.get("size", 0)
            result.append(f"- [{item_type}] {name} ({size} bytes)")
        
        return "\n".join(result)
    
    def get_file_content(self, item_id: str) -> bytes:
        """Get file content by item ID.
        
        Args:
            item_id: The ID of the file
        
        Returns:
            File content as bytes
        """
        return self.client.download_file(item_id)
    
    def upload_content(
        self, 
        file_path: str, 
        content: bytes,
        require_confirmation: bool = True
    ) -> str:
        """Upload content to OneDrive.
        
        WARNING: This operation will overwrite any existing file at the specified path.
        
        Args:
            file_path: Path where to upload the file
            content: File content as bytes
            require_confirmation: Whether to require user confirmation before uploading
        
        Returns:
            Success message with file information, or cancellation message
        """
        if require_confirmation:
            message = (
                f"You are about to upload a file to: {file_path}\n"
                f"File size: {len(content)} bytes\n"
                f"WARNING: This will OVERWRITE any existing file at this path!"
            )
            if not self.confirmation_callback(message):
                return f"❌ Upload cancelled by user for: {file_path}"
        
        result = self.client.upload_file(file_path, content)
        return f"✅ File uploaded successfully: {result.get('name')} (ID: {result.get('id')})"
    
    def search(self, query: str) -> str:
        """Search for items in OneDrive.
        
        Args:
            query: Search query string
        
        Returns:
            Formatted string with search results
        """
        items = self.client.search_items(query)
        if not items:
            return f"No items found matching '{query}'."
        
        result = [f"Found {len(items)} item(s):"]
        for item in items[:10]:  # Limit to 10 results
            item_type = "Folder" if "folder" in item else "File"
            name = item.get("name", "Unknown")
            result.append(f"- [{item_type}] {name} (ID: {item.get('id')})")
        
        if len(items) > 10:
            result.append(f"... and {len(items) - 10} more items")
        
        return "\n".join(result)
    
    def create_folder(
        self, 
        folder_name: str, 
        parent_path: str = "",
        conflict_behavior: str = "rename"
    ) -> str:
        """Create a new folder in OneDrive.
        
        Args:
            folder_name: Name of the folder to create
            parent_path: Path to parent folder (empty for root)
            conflict_behavior: How to handle naming conflicts ("rename", "replace", or "fail")
        
        Returns:
            Success message with folder information
        """
        result = self.client.create_folder(folder_name, parent_path, conflict_behavior)
        location = f"in '{parent_path}'" if parent_path else "in root"
        return f"✅ Folder created successfully: {result.get('name')} (ID: {result.get('id')}) {location}"
    
    def delete_item(
        self, 
        item_id: str,
        item_name: Optional[str] = None,
        require_confirmation: bool = True
    ) -> str:
        """Delete a file or folder from OneDrive.
        
        ⚠️ WARNING: This is a DESTRUCTIVE operation that permanently deletes the item.
        
        Args:
            item_id: The ID of the item to delete
            item_name: Optional name of the item for better confirmation message
            require_confirmation: Whether to require user confirmation before deleting
        
        Returns:
            Success message or cancellation message
        """
        if require_confirmation:
            # If item_name not provided, try to get it
            display_name = item_name
            if not display_name:
                try:
                    item_info = self.client.get_item_info(item_id)
                    display_name = item_info.get('name', 'Unknown item')
                except Exception:
                    display_name = f"item with ID {item_id}"
            
            message = (
                f"⚠️  DESTRUCTIVE OPERATION ⚠️\n"
                f"You are about to PERMANENTLY DELETE: {display_name}\n"
                f"Item ID: {item_id}\n"
                f"This action CANNOT be undone!"
            )
            if not self.confirmation_callback(message):
                return f"❌ Deletion cancelled by user for: {display_name}"
        
        self.client.delete_item(item_id)
        display_name = item_name or f"item {item_id}"
        return f"✅ Item deleted successfully: {display_name}"
