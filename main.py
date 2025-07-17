#!/usr/bin/env python3
"""
Google Drive API v3 MCP Server
A comprehensive MCP server with structured output for all Google Drive API v3 endpoints.
Uses Nango for authentication.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize FastMCP server
mcp = FastMCP("Google Drive API v3")

# Base URL for Google Drive API
BASE_URL = "https://www.googleapis.com"

# Global variable to cache access token
_cached_access_token = None

def get_connection_credentials() -> dict[str, Any]:
    """Get credentials from Nango"""

    id = os.environ.get("NANGO_CONNECTION_ID")
    integration_id = os.environ.get("NANGO_INTEGRATION_ID")
    base_url = os.environ.get("NANGO_BASE_URL")
    secret_key = os.environ.get("NANGO_SECRET_KEY")
    
    url = f"{base_url}/connection/{id}"
    params = {
        "provider_config_key": integration_id,
        "refresh_token": "true",
    }
    headers = {"Authorization": f"Bearer {secret_key}"}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise exception for bad status codes
    
    return response.json()

def get_access_token() -> str:
    """Get access token from Nango, with caching"""
    global _cached_access_token
    
    if _cached_access_token is None:
        credentials = get_connection_credentials()
        _cached_access_token = credentials.get("credentials", {}).get("access_token")
        
        if not _cached_access_token:
            raise ValueError("No access token found in Nango credentials")
    
    return _cached_access_token

def refresh_access_token() -> str:
    """Force refresh access token from Nango"""
    global _cached_access_token
    _cached_access_token = None
    return get_access_token()

# Structured output models
class APIResponse(BaseModel):
    """Standard API response structure"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class FileMetadata(BaseModel):
    """File metadata structure"""
    id: Optional[str] = None
    name: Optional[str] = None
    mimeType: Optional[str] = None
    parents: Optional[List[str]] = None
    createdTime: Optional[str] = None
    modifiedTime: Optional[str] = None
    size: Optional[str] = None
    webViewLink: Optional[str] = None
    webContentLink: Optional[str] = None

class FileList(BaseModel):
    """File list response structure"""
    files: List[FileMetadata] = Field(default_factory=list)
    nextPageToken: Optional[str] = None
    incompleteSearch: Optional[bool] = None

class Permission(BaseModel):
    """Permission structure"""
    id: Optional[str] = None
    type: Optional[str] = None
    role: Optional[str] = None
    emailAddress: Optional[str] = None
    displayName: Optional[str] = None

class PermissionList(BaseModel):
    """Permission list response structure"""
    permissions: List[Permission] = Field(default_factory=list)
    nextPageToken: Optional[str] = None

class Comment(BaseModel):
    """Comment structure"""
    id: Optional[str] = None
    content: Optional[str] = None
    author: Optional[Dict[str, str]] = None
    createdTime: Optional[str] = None
    modifiedTime: Optional[str] = None

class CommentList(BaseModel):
    """Comment list response structure"""
    comments: List[Comment] = Field(default_factory=list)
    nextPageToken: Optional[str] = None

class Reply(BaseModel):
    """Reply structure"""
    id: Optional[str] = None
    content: Optional[str] = None
    author: Optional[Dict[str, str]] = None
    createdTime: Optional[str] = None
    modifiedTime: Optional[str] = None

class ReplyList(BaseModel):
    """Reply list response structure"""
    replies: List[Reply] = Field(default_factory=list)
    nextPageToken: Optional[str] = None

class Drive(BaseModel):
    """Shared drive structure"""
    id: Optional[str] = None
    name: Optional[str] = None
    createdTime: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None

class DriveList(BaseModel):
    """Drive list response structure"""
    drives: List[Drive] = Field(default_factory=list)
    nextPageToken: Optional[str] = None

class Revision(BaseModel):
    """Revision structure"""
    id: Optional[str] = None
    mimeType: Optional[str] = None
    modifiedTime: Optional[str] = None
    size: Optional[str] = None

class RevisionList(BaseModel):
    """Revision list response structure"""
    revisions: List[Revision] = Field(default_factory=list)
    nextPageToken: Optional[str] = None

class AccessProposal(BaseModel):
    """Access proposal structure"""
    id: Optional[str] = None
    requestMessage: Optional[str] = None
    requestingUser: Optional[Dict[str, str]] = None

class AccessProposalList(BaseModel):
    """Access proposal list response structure"""
    accessProposals: List[AccessProposal] = Field(default_factory=list)
    nextPageToken: Optional[str] = None

class App(BaseModel):
    """App structure"""
    id: Optional[str] = None
    name: Optional[str] = None
    productName: Optional[str] = None
    authorized: Optional[bool] = None

class AppList(BaseModel):
    """App list response structure"""
    apps: List[App] = Field(default_factory=list)

class Change(BaseModel):
    """Change structure"""
    changeType: Optional[str] = None
    file: Optional[FileMetadata] = None
    fileId: Optional[str] = None
    time: Optional[str] = None

class ChangeList(BaseModel):
    """Change list response structure"""
    changes: List[Change] = Field(default_factory=list)
    nextPageToken: Optional[str] = None
    newStartPageToken: Optional[str] = None

class Operation(BaseModel):
    """Long-running operation structure"""
    name: Optional[str] = None
    done: Optional[bool] = None
    error: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None

# Helper function to make API requests
def make_api_request(
    method: str,
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    retry_auth: bool = True
) -> APIResponse:
    """Make HTTP request to Google Drive API with automatic token refresh"""
    url = f"{BASE_URL}{endpoint}"
    
    # Get access token if not provided in headers
    if not headers or "Authorization" not in headers:
        try:
            access_token = get_access_token()
            if not headers:
                headers = {}
            headers["Authorization"] = f"Bearer {access_token}"
        except Exception as e:
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                error=f"Failed to get access token: {str(e)}"
            )
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            data=data,
            timeout=30
        )
        
        # If we get a 401 and retry_auth is True, try to refresh the token
        if response.status_code == 401 and retry_auth:
            try:
                access_token = refresh_access_token()
                headers["Authorization"] = f"Bearer {access_token}"
                # Retry the request with the new token
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    data=data,
                    timeout=30
                )
            except Exception as e:
                return APIResponse(
                    success=False,
                    status_code=401,
                    data=None,
                    error=f"Failed to refresh access token: {str(e)}"
                )
        
        response_data = None
        if response.content:
            try:
                response_data = response.json()
            except:
                response_data = {"content": response.text}
        
        return APIResponse(
            success=response.ok,
            status_code=response.status_code,
            data=response_data,
            error=None if response.ok else f"HTTP {response.status_code}: {response.reason}"
        )
    except requests.exceptions.RequestException as e:
        return APIResponse(
            success=False,
            status_code=0,
            data=None,
            error=str(e)
        )

# About resource tools
@mcp.tool()
def about_get(
    fields: Optional[str] = None
) -> APIResponse:
    """Gets information about the user, the user's Drive, and system capabilities."""
    params = {}
    if fields:
        params["fields"] = fields
    
    return make_api_request("GET", "/drive/v3/about", params=params)

# Access proposals resource tools
@mcp.tool()
def accessproposals_get(
    file_id: str,
    proposal_id: str
) -> APIResponse:
    """Retrieves an AccessProposal by ID."""
    endpoint = f"/drive/v3/files/{file_id}/accessproposals/{proposal_id}"
    return make_api_request("GET", endpoint)

@mcp.tool()
def accessproposals_list(
    file_id: str,
    page_token: Optional[str] = None,
    page_size: Optional[int] = None
) -> AccessProposalList:
    """List the AccessProposals on a file."""
    params = {}
    if page_token:
        params["pageToken"] = page_token
    if page_size:
        params["pageSize"] = page_size
    
    endpoint = f"/drive/v3/files/{file_id}/accessproposals"
    response = make_api_request("GET", endpoint, params=params)
    
    if response.success and response.data:
        return AccessProposalList(
            accessProposals=[AccessProposal(**item) for item in response.data.get("accessProposals", [])],
            nextPageToken=response.data.get("nextPageToken")
        )
    else:
        return AccessProposalList()

@mcp.tool()
def accessproposals_resolve(
    file_id: str,
    proposal_id: str,
    action: str,
    send_notification: Optional[bool] = None
) -> APIResponse:
    """Used to approve or deny an Access Proposal."""
    json_data = {"action": action}
    if send_notification is not None:
        json_data["sendNotification"] = send_notification
    
    endpoint = f"/drive/v3/files/{file_id}/accessproposals/{proposal_id}:resolve"
    return make_api_request("POST", endpoint, json_data=json_data)

# Apps resource tools
@mcp.tool()
def apps_get(
    app_id: str
) -> APIResponse:
    """Gets a specific app."""
    endpoint = f"/drive/v3/apps/{app_id}"
    return make_api_request("GET", endpoint)

@mcp.tool()
def apps_list(
    app_filter_extensions: Optional[str] = None,
    app_filter_mime_types: Optional[str] = None,
    language_code: Optional[str] = None
) -> AppList:
    """Lists a user's installed apps."""
    params = {}
    if app_filter_extensions:
        params["appFilterExtensions"] = app_filter_extensions
    if app_filter_mime_types:
        params["appFilterMimeTypes"] = app_filter_mime_types
    if language_code:
        params["languageCode"] = language_code
    
    response = make_api_request("GET", "/drive/v3/apps", params=params)
    
    if response.success and response.data:
        return AppList(
            apps=[App(**item) for item in response.data.get("apps", [])]
        )
    else:
        return AppList()

# Changes resource tools
@mcp.tool()
def changes_get_start_page_token(
    drive_id: Optional[str] = None,
    supports_all_drives: Optional[bool] = None
) -> APIResponse:
    """Gets the starting pageToken for listing future changes."""
    params = {}
    if drive_id:
        params["driveId"] = drive_id
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    
    return make_api_request("GET", "/drive/v3/changes/startPageToken", params=params)

@mcp.tool()
def changes_list(
    page_token: str,
    drive_id: Optional[str] = None,
    include_corpus_removals: Optional[bool] = None,
    include_items_from_all_drives: Optional[bool] = None,
    include_removed: Optional[bool] = None,
    page_size: Optional[int] = None,
    restrict_to_my_drive: Optional[bool] = None,
    spaces: Optional[str] = None,
    supports_all_drives: Optional[bool] = None
) -> ChangeList:
    """Lists the changes for a user or shared drive."""
    params = {"pageToken": page_token}
    
    if drive_id:
        params["driveId"] = drive_id
    if include_corpus_removals is not None:
        params["includeCorpusRemovals"] = include_corpus_removals
    if include_items_from_all_drives is not None:
        params["includeItemsFromAllDrives"] = include_items_from_all_drives
    if include_removed is not None:
        params["includeRemoved"] = include_removed
    if page_size:
        params["pageSize"] = page_size
    if restrict_to_my_drive is not None:
        params["restrictToMyDrive"] = restrict_to_my_drive
    if spaces:
        params["spaces"] = spaces
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    
    response = make_api_request("GET", "/drive/v3/changes", params=params)
    
    if response.success and response.data:
        return ChangeList(
            changes=[Change(**item) for item in response.data.get("changes", [])],
            nextPageToken=response.data.get("nextPageToken"),
            newStartPageToken=response.data.get("newStartPageToken")
        )
    else:
        return ChangeList()

@mcp.tool()
def changes_watch(
    page_token: str,
    channel_id: str,
    channel_type: str,
    address: str,
    drive_id: Optional[str] = None,
    include_corpus_removals: Optional[bool] = None,
    include_items_from_all_drives: Optional[bool] = None,
    include_removed: Optional[bool] = None,
    page_size: Optional[int] = None,
    restrict_to_my_drive: Optional[bool] = None,
    spaces: Optional[str] = None,
    supports_all_drives: Optional[bool] = None
) -> APIResponse:
    """Subscribes to changes for a user."""
    params = {"pageToken": page_token}
    
    if drive_id:
        params["driveId"] = drive_id
    if include_corpus_removals is not None:
        params["includeCorpusRemovals"] = include_corpus_removals
    if include_items_from_all_drives is not None:
        params["includeItemsFromAllDrives"] = include_items_from_all_drives
    if include_removed is not None:
        params["includeRemoved"] = include_removed
    if page_size:
        params["pageSize"] = page_size
    if restrict_to_my_drive is not None:
        params["restrictToMyDrive"] = restrict_to_my_drive
    if spaces:
        params["spaces"] = spaces
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    
    json_data = {
        "id": channel_id,
        "type": channel_type,
        "address": address
    }
    
    return make_api_request("POST", "/drive/v3/changes/watch", params=params, json_data=json_data)

# Channels resource tools
@mcp.tool()
def channels_stop(
    channel_id: str,
    resource_id: str
) -> APIResponse:
    """Stops watching resources through this channel."""
    json_data = {
        "id": channel_id,
        "resourceId": resource_id
    }
    
    return make_api_request("POST", "/drive/v3/channels/stop", json_data=json_data)

# Comments resource tools
@mcp.tool()
def comments_create(
    file_id: str,
    content: str,
    anchor: Optional[str] = None,
    quoted_file_content: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """Creates a comment on a file."""
    json_data = {"content": content}
    if anchor:
        json_data["anchor"] = anchor
    if quoted_file_content:
        json_data["quotedFileContent"] = quoted_file_content
    
    endpoint = f"/drive/v3/files/{file_id}/comments"
    return make_api_request("POST", endpoint, json_data=json_data)

@mcp.tool()
def comments_delete(
    file_id: str,
    comment_id: str
) -> APIResponse:
    """Deletes a comment."""
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}"
    return make_api_request("DELETE", endpoint)

@mcp.tool()
def comments_get(
    file_id: str,
    comment_id: str,
    include_deleted: Optional[bool] = None
) -> APIResponse:
    """Gets a comment by ID."""
    params = {}
    if include_deleted is not None:
        params["includeDeleted"] = include_deleted
    
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def comments_list(
    file_id: str,
    include_deleted: Optional[bool] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
    start_modified_time: Optional[str] = None
) -> CommentList:
    """Lists a file's comments."""
    params = {}
    if include_deleted is not None:
        params["includeDeleted"] = include_deleted
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token
    if start_modified_time:
        params["startModifiedTime"] = start_modified_time
    
    endpoint = f"/drive/v3/files/{file_id}/comments"
    response = make_api_request("GET", endpoint, params=params)
    
    if response.success and response.data:
        return CommentList(
            comments=[Comment(**item) for item in response.data.get("comments", [])],
            nextPageToken=response.data.get("nextPageToken")
        )
    else:
        return CommentList()

@mcp.tool()
def comments_update(
    file_id: str,
    comment_id: str,
    content: str
) -> APIResponse:
    """Updates a comment with patch semantics."""
    json_data = {"content": content}
    
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}"
    return make_api_request("PATCH", endpoint, json_data=json_data)

# Drives resource tools
@mcp.tool()
def drives_create(
    request_id: str,
    name: str,
    hidden: Optional[bool] = None
) -> APIResponse:
    """Creates a shared drive."""
    params = {"requestId": request_id}
    json_data = {"name": name}
    if hidden is not None:
        json_data["hidden"] = hidden
    
    return make_api_request("POST", "/drive/v3/drives", params=params, json_data=json_data)

@mcp.tool()
def drives_delete(
    drive_id: str,
    use_domain_admin_access: Optional[bool] = None,
    allow_item_deletion: Optional[bool] = None
) -> APIResponse:
    """Permanently deletes a shared drive for which the user is an organizer."""
    params = {}
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    if allow_item_deletion is not None:
        params["allowItemDeletion"] = allow_item_deletion
    
    endpoint = f"/drive/v3/drives/{drive_id}"
    return make_api_request("DELETE", endpoint, params=params)

@mcp.tool()
def drives_get(
    drive_id: str,
    use_domain_admin_access: Optional[bool] = None
) -> APIResponse:
    """Gets a shared drive's metadata by ID."""
    params = {}
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    endpoint = f"/drive/v3/drives/{drive_id}"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def drives_hide(
    drive_id: str
) -> APIResponse:
    """Hides a shared drive from the default view."""
    endpoint = f"/drive/v3/drives/{drive_id}/hide"
    return make_api_request("POST", endpoint)

@mcp.tool()
def drives_list(
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
    q: Optional[str] = None,
    use_domain_admin_access: Optional[bool] = None
) -> DriveList:
    """Lists the user's shared drives."""
    params = {}
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token
    if q:
        params["q"] = q
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    response = make_api_request("GET", "/drive/v3/drives", params=params)
    
    if response.success and response.data:
        return DriveList(
            drives=[Drive(**item) for item in response.data.get("drives", [])],
            nextPageToken=response.data.get("nextPageToken")
        )
    else:
        return DriveList()

@mcp.tool()
def drives_unhide(
    drive_id: str
) -> APIResponse:
    """Restores a shared drive to the default view."""
    endpoint = f"/drive/v3/drives/{drive_id}/unhide"
    return make_api_request("POST", endpoint)

@mcp.tool()
def drives_update(
    drive_id: str,
    name: Optional[str] = None,
    use_domain_admin_access: Optional[bool] = None
) -> APIResponse:
    """Updates the metadata for a shared drive."""
    params = {}
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    json_data = {}
    if name:
        json_data["name"] = name
    
    endpoint = f"/drive/v3/drives/{drive_id}"
    return make_api_request("PATCH", endpoint, params=params, json_data=json_data)

# Files resource tools
@mcp.tool()
def files_copy(
    file_id: str,
    name: Optional[str] = None,
    parents: Optional[List[str]] = None,
    ignore_default_visibility: Optional[bool] = None,
    keep_revision_forever: Optional[bool] = None,
    ocr_language: Optional[str] = None,
    supports_all_drives: Optional[bool] = None
) -> APIResponse:
    """Creates a copy of a file and applies any requested updates with patch semantics."""
    params = {}
    if ignore_default_visibility is not None:
        params["ignoreDefaultVisibility"] = ignore_default_visibility
    if keep_revision_forever is not None:
        params["keepRevisionForever"] = keep_revision_forever
    if ocr_language:
        params["ocrLanguage"] = ocr_language
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    
    json_data = {}
    if name:
        json_data["name"] = name
    if parents:
        json_data["parents"] = parents
    
    endpoint = f"/drive/v3/files/{file_id}/copy"
    return make_api_request("POST", endpoint, params=params, json_data=json_data)

@mcp.tool()
def files_create(
    name: str,
    parents: Optional[List[str]] = None,
    mime_type: Optional[str] = None,
    ignore_default_visibility: Optional[bool] = None,
    keep_revision_forever: Optional[bool] = None,
    ocr_language: Optional[str] = None,
    supports_all_drives: Optional[bool] = None,
    use_content_as_indexable_text: Optional[bool] = None
) -> APIResponse:
    """Creates a new file."""
    params = {}
    if ignore_default_visibility is not None:
        params["ignoreDefaultVisibility"] = ignore_default_visibility
    if keep_revision_forever is not None:
        params["keepRevisionForever"] = keep_revision_forever
    if ocr_language:
        params["ocrLanguage"] = ocr_language
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if use_content_as_indexable_text is not None:
        params["useContentAsIndexableText"] = use_content_as_indexable_text
    
    json_data = {"name": name}
    if parents:
        json_data["parents"] = parents
    if mime_type:
        json_data["mimeType"] = mime_type
    
    return make_api_request("POST", "/upload/drive/v3/files", params=params, json_data=json_data)

@mcp.tool()
def files_delete(
    file_id: str,
    supports_all_drives: Optional[bool] = None
) -> APIResponse:
    """Permanently deletes a file owned by the user without moving it to the trash."""
    params = {}
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    
    endpoint = f"/drive/v3/files/{file_id}"
    return make_api_request("DELETE", endpoint, params=params)

@mcp.tool()
def files_download(
    file_id: str,
    mime_type: Optional[str] = None,
    revision_id: Optional[str] = None
) -> APIResponse:
    """Downloads content of a file."""
    params = {}
    if mime_type:
        params["mimeType"] = mime_type
    if revision_id:
        params["revisionId"] = revision_id
    
    endpoint = f"/drive/v3/files/{file_id}/download"
    return make_api_request("POST", endpoint, params=params)

@mcp.tool()
def files_empty_trash(
    drive_id: Optional[str] = None
) -> APIResponse:
    """Permanently deletes all of the user's trashed files."""
    params = {}
    if drive_id:
        params["driveId"] = drive_id
    
    return make_api_request("DELETE", "/drive/v3/files/trash", params=params)

@mcp.tool()
def files_export(
    file_id: str,
    mime_type: str
) -> APIResponse:
    """Exports a Google Workspace document to the requested MIME type and returns exported byte content."""
    params = {"mimeType": mime_type}
    
    endpoint = f"/drive/v3/files/{file_id}/export"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def files_generate_ids(
    count: Optional[int] = None,
    space: Optional[str] = None,
    type: Optional[str] = None
) -> APIResponse:
    """Generates a set of file IDs which can be provided in create or copy requests."""
    params = {}
    if count:
        params["count"] = count
    if space:
        params["space"] = space
    if type:
        params["type"] = type
    
    return make_api_request("GET", "/drive/v3/files/generateIds", params=params)

@mcp.tool()
def files_get(
    file_id: str,
    acknowledge_abuse: Optional[bool] = None,
    supports_all_drives: Optional[bool] = None,
    fields: Optional[str] = None
) -> APIResponse:
    """Gets a file's metadata or content by ID."""
    params = {}
    if acknowledge_abuse is not None:
        params["acknowledgeAbuse"] = acknowledge_abuse
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if fields:
        params["fields"] = fields
    
    endpoint = f"/drive/v3/files/{file_id}"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def files_list(
    corpora: Optional[str] = None,
    drive_id: Optional[str] = None,
    include_items_from_all_drives: Optional[bool] = None,
    order_by: Optional[str] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
    q: Optional[str] = None,
    spaces: Optional[str] = None,
    supports_all_drives: Optional[bool] = None
) -> FileList:
    """Lists the user's files."""
    params = {}
    if corpora:
        params["corpora"] = corpora
    if drive_id:
        params["driveId"] = drive_id
    if include_items_from_all_drives is not None:
        params["includeItemsFromAllDrives"] = include_items_from_all_drives
    if order_by:
        params["orderBy"] = order_by
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token
    if q:
        params["q"] = q
    if spaces:
        params["spaces"] = spaces
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    
    response = make_api_request("GET", "/drive/v3/files", params=params)
    
    if response.success and response.data:
        return FileList(
            files=[FileMetadata(**item) for item in response.data.get("files", [])],
            nextPageToken=response.data.get("nextPageToken"),
            incompleteSearch=response.data.get("incompleteSearch")
        )
    else:
        return FileList()

@mcp.tool()
def files_list_labels(
    file_id: str,
    max_results: Optional[int] = None,
    page_token: Optional[str] = None
) -> APIResponse:
    """Lists the labels on a file."""
    params = {}
    if max_results:
        params["maxResults"] = max_results
    if page_token:
        params["pageToken"] = page_token
    
    endpoint = f"/drive/v3/files/{file_id}/listLabels"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def files_modify_labels(
    file_id: str,
    label_modifications: List[Dict[str, Any]]
) -> APIResponse:
    """Modifies the set of labels applied to a file."""
    json_data = {"labelModifications": label_modifications}
    
    endpoint = f"/drive/v3/files/{file_id}/modifyLabels"
    return make_api_request("POST", endpoint, json_data=json_data)

@mcp.tool()
def files_update(
    file_id: str,
    name: Optional[str] = None,
    add_parents: Optional[str] = None,
    remove_parents: Optional[str] = None,
    keep_revision_forever: Optional[bool] = None,
    ocr_language: Optional[str] = None,
    supports_all_drives: Optional[bool] = None,
    use_content_as_indexable_text: Optional[bool] = None
) -> APIResponse:
    """Updates a file's metadata and/or content."""
    params = {}
    if add_parents:
        params["addParents"] = add_parents
    if remove_parents:
        params["removeParents"] = remove_parents
    if keep_revision_forever is not None:
        params["keepRevisionForever"] = keep_revision_forever
    if ocr_language:
        params["ocrLanguage"] = ocr_language
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if use_content_as_indexable_text is not None:
        params["useContentAsIndexableText"] = use_content_as_indexable_text
    
    json_data = {}
    if name:
        json_data["name"] = name
    
    endpoint = f"/upload/drive/v3/files/{file_id}"
    return make_api_request("PATCH", endpoint, params=params, json_data=json_data)

@mcp.tool()
def files_watch(
    file_id: str,
    channel_id: str,
    channel_type: str,
    address: str,
    supports_all_drives: Optional[bool] = None,
    acknowledge_abuse: Optional[bool] = None
) -> APIResponse:
    """Subscribes to changes to a file."""
    params = {}
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if acknowledge_abuse is not None:
        params["acknowledgeAbuse"] = acknowledge_abuse
    
    json_data = {
        "id": channel_id,
        "type": channel_type,
        "address": address
    }
    
    endpoint = f"/drive/v3/files/{file_id}/watch"
    return make_api_request("POST", endpoint, params=params, json_data=json_data).tool()
def files_modify_labels(
    file_id: str,
    access_token: str,
    label_modifications: List[Dict[str, Any]]
) -> APIResponse:
    """Modifies the set of labels applied to a file."""
    headers = {"Authorization": f"Bearer {access_token}"}
    json_data = {"labelModifications": label_modifications}
    
    endpoint = f"/drive/v3/files/{file_id}/modifyLabels"
    return make_api_request("POST", endpoint, headers=headers, json_data=json_data)

@mcp.tool()
def files_update(
    file_id: str,
    access_token: str,
    name: Optional[str] = None,
    add_parents: Optional[str] = None,
    remove_parents: Optional[str] = None,
    keep_revision_forever: Optional[bool] = None,
    ocr_language: Optional[str] = None,
    supports_all_drives: Optional[bool] = None,
    use_content_as_indexable_text: Optional[bool] = None
) -> APIResponse:
    """Updates a file's metadata and/or content."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {}
    if add_parents:
        params["addParents"] = add_parents
    if remove_parents:
        params["removeParents"] = remove_parents
    if keep_revision_forever is not None:
        params["keepRevisionForever"] = keep_revision_forever
    if ocr_language:
        params["ocrLanguage"] = ocr_language
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if use_content_as_indexable_text is not None:
        params["useContentAsIndexableText"] = use_content_as_indexable_text
    
    json_data = {}
    if name:
        json_data["name"] = name
    
    endpoint = f"/upload/drive/v3/files/{file_id}"
    return make_api_request("PATCH", endpoint, headers=headers, params=params, json_data=json_data)

@mcp.tool()
def files_watch(
    file_id: str,
    access_token: str,
    channel_id: str,
    channel_type: str,
    address: str,
    supports_all_drives: Optional[bool] = None,
    acknowledge_abuse: Optional[bool] = None
) -> APIResponse:
    """Subscribes to changes to a file."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {}
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if acknowledge_abuse is not None:
        params["acknowledgeAbuse"] = acknowledge_abuse
    
    json_data = {
        "id": channel_id,
        "type": channel_type,
        "address": address
    }
    
    endpoint = f"/drive/v3/files/{file_id}/watch"
    return make_api_request("POST", endpoint, headers=headers, params=params, json_data=json_data)

# Operations resource tools
@mcp.tool()
def operations_get(
    name: str
) -> Operation:
    """Gets the latest state of a long-running operation."""
    endpoint = f"/drive/v3/operations/{name}"
    
    response = make_api_request("GET", endpoint)
    
    if response.success and response.data:
        return Operation(**response.data)
    else:
        return Operation()

# Permissions resource tools
@mcp.tool()
def permissions_create(
    file_id: str,
    role: str,
    type: str,
    email_address: Optional[str] = None,
    domain: Optional[str] = None,
    email_message: Optional[str] = None,
    move_to_new_owners_root: Optional[bool] = None,
    send_notification_email: Optional[bool] = None,
    supports_all_drives: Optional[bool] = None,
    transfer_ownership: Optional[bool] = None,
    use_domain_admin_access: Optional[bool] = None
) -> APIResponse:
    """Creates a permission for a file or shared drive."""
    params = {}
    if email_message:
        params["emailMessage"] = email_message
    if move_to_new_owners_root is not None:
        params["moveToNewOwnersRoot"] = move_to_new_owners_root
    if send_notification_email is not None:
        params["sendNotificationEmail"] = send_notification_email
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if transfer_ownership is not None:
        params["transferOwnership"] = transfer_ownership
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    json_data = {
        "role": role,
        "type": type
    }
    if email_address:
        json_data["emailAddress"] = email_address
    if domain:
        json_data["domain"] = domain
    
    endpoint = f"/drive/v3/files/{file_id}/permissions"
    return make_api_request("POST", endpoint, params=params, json_data=json_data)

@mcp.tool()
def permissions_delete(
    file_id: str,
    permission_id: str,
    supports_all_drives: Optional[bool] = None,
    use_domain_admin_access: Optional[bool] = None
) -> APIResponse:
    """Deletes a permission."""
    params = {}
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    endpoint = f"/drive/v3/files/{file_id}/permissions/{permission_id}"
    return make_api_request("DELETE", endpoint, params=params)

@mcp.tool()
def permissions_get(
    file_id: str,
    permission_id: str,
    supports_all_drives: Optional[bool] = None,
    use_domain_admin_access: Optional[bool] = None
) -> APIResponse:
    """Gets a permission by ID."""
    params = {}
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    endpoint = f"/drive/v3/files/{file_id}/permissions/{permission_id}"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def permissions_list(
    file_id: str,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None,
    supports_all_drives: Optional[bool] = None,
    use_domain_admin_access: Optional[bool] = None
) -> PermissionList:
    """Lists a file's or shared drive's permissions."""
    params = {}
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    endpoint = f"/drive/v3/files/{file_id}/permissions"
    response = make_api_request("GET", endpoint, params=params)
    
    if response.success and response.data:
        return PermissionList(
            permissions=[Permission(**item) for item in response.data.get("permissions", [])],
            nextPageToken=response.data.get("nextPageToken")
        )
    else:
        return PermissionList()

@mcp.tool()
def permissions_update(
    file_id: str,
    permission_id: str,
    role: Optional[str] = None,
    remove_expiration: Optional[bool] = None,
    supports_all_drives: Optional[bool] = None,
    transfer_ownership: Optional[bool] = None,
    use_domain_admin_access: Optional[bool] = None
) -> APIResponse:
    """Updates a permission with patch semantics."""
    params = {}
    if remove_expiration is not None:
        params["removeExpiration"] = remove_expiration
    if supports_all_drives is not None:
        params["supportsAllDrives"] = supports_all_drives
    if transfer_ownership is not None:
        params["transferOwnership"] = transfer_ownership
    if use_domain_admin_access is not None:
        params["useDomainAdminAccess"] = use_domain_admin_access
    
    json_data = {}
    if role:
        json_data["role"] = role
    
    endpoint = f"/drive/v3/files/{file_id}/permissions/{permission_id}"
    return make_api_request("PATCH", endpoint, params=params, json_data=json_data)

# Replies resource tools
@mcp.tool()
def replies_create(
    file_id: str,
    comment_id: str,
    content: str
) -> APIResponse:
    """Creates a reply to a comment."""
    json_data = {"content": content}
    
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}/replies"
    return make_api_request("POST", endpoint, json_data=json_data)

@mcp.tool()
def replies_delete(
    file_id: str,
    comment_id: str,
    reply_id: str
) -> APIResponse:
    """Deletes a reply."""
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}/replies/{reply_id}"
    return make_api_request("DELETE", endpoint)

@mcp.tool()
def replies_get(
    file_id: str,
    comment_id: str,
    reply_id: str,
    include_deleted: Optional[bool] = None
) -> APIResponse:
    """Gets a reply by ID."""
    params = {}
    if include_deleted is not None:
        params["includeDeleted"] = include_deleted
    
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}/replies/{reply_id}"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def replies_list(
    file_id: str,
    comment_id: str,
    include_deleted: Optional[bool] = None,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None
) -> ReplyList:
    """Lists a comment's replies."""
    params = {}
    if include_deleted is not None:
        params["includeDeleted"] = include_deleted
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token
    
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}/replies"
    response = make_api_request("GET", endpoint, params=params)
    
    if response.success and response.data:
        return ReplyList(
            replies=[Reply(**item) for item in response.data.get("replies", [])],
            nextPageToken=response.data.get("nextPageToken")
        )
    else:
        return ReplyList()

@mcp.tool()
def replies_update(
    file_id: str,
    comment_id: str,
    reply_id: str,
    content: str
) -> APIResponse:
    """Updates a reply with patch semantics."""
    json_data = {"content": content}
    
    endpoint = f"/drive/v3/files/{file_id}/comments/{comment_id}/replies/{reply_id}"
    return make_api_request("PATCH", endpoint, json_data=json_data)

# Revisions resource tools
@mcp.tool()
def revisions_delete(
    file_id: str,
    revision_id: str
) -> APIResponse:
    """Permanently deletes a file version."""
    endpoint = f"/drive/v3/files/{file_id}/revisions/{revision_id}"
    return make_api_request("DELETE", endpoint)

@mcp.tool()
def revisions_get(
    file_id: str,
    revision_id: str,
    acknowledge_abuse: Optional[bool] = None
) -> APIResponse:
    """Gets a revision's metadata or content by ID."""
    params = {}
    if acknowledge_abuse is not None:
        params["acknowledgeAbuse"] = acknowledge_abuse
    
    endpoint = f"/drive/v3/files/{file_id}/revisions/{revision_id}"
    return make_api_request("GET", endpoint, params=params)

@mcp.tool()
def revisions_list(
    file_id: str,
    page_size: Optional[int] = None,
    page_token: Optional[str] = None
) -> RevisionList:
    """Lists a file's revisions."""
    params = {}
    if page_size:
        params["pageSize"] = page_size
    if page_token:
        params["pageToken"] = page_token
    
    endpoint = f"/drive/v3/files/{file_id}/revisions"
    response = make_api_request("GET", endpoint, params=params)
    
    if response.success and response.data:
        return RevisionList(
            revisions=[Revision(**item) for item in response.data.get("revisions", [])],
            nextPageToken=response.data.get("nextPageToken")
        )
    else:
        return RevisionList()

@mcp.tool()
def revisions_update(
    file_id: str,
    revision_id: str,
    keep_forever: Optional[bool] = None,
    published: Optional[bool] = None,
    published_outside_domain: Optional[bool] = None
) -> APIResponse:
    """Updates a revision with patch semantics."""
    json_data = {}
    if keep_forever is not None:
        json_data["keepForever"] = keep_forever
    if published is not None:
        json_data["published"] = published
    if published_outside_domain is not None:
        json_data["publishedOutsideDomain"] = published_outside_domain
    
    endpoint = f"/drive/v3/files/{file_id}/revisions/{revision_id}"
    return make_api_request("PATCH", endpoint, json_data=json_data)

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()