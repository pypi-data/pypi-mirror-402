"""OneDrive Skill - A Python skill for connecting to Microsoft OneDrive.

This package provides a skill interface for LLMs to interact with OneDrive
using the Microsoft Graph API. Authentication tokens must be provided via
environment variables or secrets.

The skill follows best practices for LLM agent skills:
- Clear metadata and descriptions for LLM discovery
- User confirmation required for destructive operations
- Safe handling of authentication tokens
- Proper error handling and user feedback
"""

from .onedrive_client import OneDriveClient, OneDriveSkill

__version__ = "0.1.0"
__all__ = ["OneDriveClient", "OneDriveSkill"]

# Skill metadata for LLM discovery
SKILL_METADATA = {
    "name": "onedrive-connect",
    "version": __version__,
    "description": "Connect to Microsoft OneDrive for file operations",
    "capabilities": [
        "list_files",
        "search",
        "get_file_content",
        "upload_content",
        "create_folder",
        "delete_item"
    ],
    "safety_features": [
        "user_confirmation_for_destructive_operations",
        "url_encoding_for_user_inputs",
        "secure_token_handling"
    ]
}

