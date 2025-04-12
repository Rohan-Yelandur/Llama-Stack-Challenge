import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import json
import logging
import io

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    """Authenticate with Google Drive and return credentials"""
    # Add authorization_prompt_message to make it clear what's happening
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', 
        SCOPES
    )
    
    st.write("Starting OAuth flow...")
    try:
        # Use the run_local_server with more explicit parameters
        creds = flow.run_local_server(
            port=3000,
            prompt='consent',  # Force re-consent to avoid cached state issues
            authorization_prompt_message="Please complete authentication in your browser"
        )
        st.write("Authentication successful!")
        
        # Get tokens
        token_info = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
        
        return creds, token_info
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        raise RuntimeError(f"Authentication failed: {str(e)}. Try clearing your browser cookies and cache.")

def get_drive_service(creds):
    """Build and return the Drive API service"""
    return build('drive', 'v3', credentials=creds)

def create_folder(service, folder_name, parent_id=None):
    """Create a folder in Google Drive.
    
    Args:
        service: Google Drive API service instance
        folder_name: Name of the folder to create
        parent_id: (Optional) ID of the parent folder
        
    Returns:
        ID of the created folder
    """
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    # If a parent folder is specified, add it to the metadata
    if parent_id:
        folder_metadata['parents'] = [parent_id]
        
    print(f"Making API request to create folder: {json.dumps(folder_metadata, indent=2)}")
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    print(f"API response: {json.dumps(folder, indent=2)}")
    
    folder_id = folder.get('id')
    print(f"Folder created with ID: {folder_id}")
    
    return folder_id

def get_file_content(service, file_id):
    """
    Download and return the content of a file from Google Drive.
    
    Args:
        service: Google Drive API service instance
        file_id: ID of the file to download
        
    Returns:
        File content as bytes
    """
    try:
        # Get file metadata to check if it's a Google Workspace file
        file_metadata = service.files().get(fileId=file_id, fields='mimeType,name').execute()
        mime_type = file_metadata.get('mimeType', '')
        
        # Check if it's a Google Workspace file
        if mime_type.startswith('application/vnd.google-apps'):
            if mime_type == 'application/vnd.google-apps.document':
                # Export Google Doc as plain text
                content = service.files().export(
                    fileId=file_id, 
                    mimeType='text/plain'
                ).execute()
                return content
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Export as CSV
                content = service.files().export(
                    fileId=file_id, 
                    mimeType='text/csv'
                ).execute()
                return content
            elif mime_type == 'application/vnd.google-apps.presentation':
                # Export as PDF
                content = service.files().export(
                    fileId=file_id, 
                    mimeType='application/pdf'
                ).execute()
                return content
            else:
                # Other Google Workspace files
                raise ValueError(f"Cannot download Google Workspace file of type: {mime_type}")
        else:
            # Regular file download
            request = service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
            file_content.seek(0)
            return file_content.read()
            
    except Exception as e:
        logging.error(f"Error downloading file {file_id}: {str(e)}")
        raise
    
def list_files(service, page_size=10, query=None):
    """List files in Google Drive.
    
    Args:
        service: Google Drive API service instance
        page_size: Maximum number of files to return
        query: Search query string (see https://developers.google.com/drive/api/v3/search-files)
        
    Returns:
        List of file metadata
    """
    results = []
    page_token = None
    
    while True:
        try:
            # Build the request
            request = service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, parents, createdTime, modifiedTime, size)",
                pageToken=page_token
            )
            
            # Execute the request
            response = request.execute()
            
            # Add the files from this page to our list
            results.extend(response.get('files', []))
            
            # Get the next page token
            page_token = response.get('nextPageToken', None)
            
            # If there are no more pages, break the loop
            if page_token is None:
                break
                
        except Exception as error:
            print(f"An error occurred: {error}")
            st.error(f"An error occurred while listing files: {error}")
            break
            
    return results

def move_file(service, file_id, folder_id):
    """Move a file to a folder in Google Drive.
    
    Args:
        service: Google Drive API service instance
        file_id: ID of the file to move
        folder_id: ID of the destination folder
        
    Returns:
        Updated file metadata
    """
    # Get the file's current parents
    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))
    
    # Move the file to the new folder
    updated_file = service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    
    return updated_file

def move_file(service, file_id, folder_id):
    """Move a file to a folder in Google Drive.
    
    Args:
        service: Google Drive API service instance
        file_id: ID of the file to move
        folder_id: ID of the destination folder
        
    Returns:
        Updated file metadata
    """
    # Get the file's current parents
    file = service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))
    
    # Move the file to the new folder
    updated_file = service.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    
    return updated_file




def find_id_by_path(service, path):
    # Remove leading and trailing slashes
    path = path.strip('/')
    
    if not path:
        # Return root folder for empty path
        return 'root'
        
    parts = path.split('/')
    parent_id = 'root'  # Start from root
    
    # Navigate through each part of the path
    for i, part in enumerate(parts):
        # Determine if we're looking for the final item or a parent folder
        is_last = (i == len(parts) - 1)
        
        # Search for the item with the given name in the parent folder
        query = f"name = '{part}' and '{parent_id}' in parents and trashed = false"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            raise FileNotFoundError(f"Cannot find '{part}' in path '{path}'")
        
        # Update parent_id for next iteration
        parent_id = items[0]['id']
    
    # Return the ID of the last item found
    return parent_id

def delete_file(service, file_id):
    service.files().delete(fileId=file_id).execute()
    return True

def delete_folder(service, folder_id, recursive=True):
    if recursive:
        # Get all files and subfolders in this folder
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, mimeType)'
        ).execute()
        
        items = results.get('files', [])
        
        # Delete each item
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                delete_folder(service, item['id'], recursive=True)
            else:
                delete_file(service, item['id'])
    
    # Delete the folder itself
    service.files().delete(fileId=folder_id).execute()
    return True

def delete_by_path(service, path, is_folder=None):
    try:
        # Find the ID of the item at the specified path
        item_id = find_id_by_path(service, path)
        
        # Determine if it's a folder if not specified
        if is_folder is None:
            file_info = service.files().get(fileId=item_id, fields='mimeType').execute()
            is_folder = file_info['mimeType'] == 'application/vnd.google-apps.folder'
        
        # Delete appropriately based on type
        if is_folder:
            return delete_folder(service, item_id)
        else:
            return delete_file(service, item_id)
            
    except Exception as e:
        logging.error(f"Error deleting '{path}': {str(e)}")
        raise

def list_files(service, folder_path='/', page_size=10, query=None):
    """List files in a specific folder in Google Drive identified by path.
    
    Args:
        service: Google Drive API service instance
        folder_path: Path to the folder to list files from (e.g., '/My Folder')
        page_size: Maximum number of files to return
        query: Additional search query string
        
    Returns:
        List of file metadata
    """
    try:
        # Find the folder ID from the path
        folder_id = find_id_by_path(service, folder_path)
        
        # Build folder-specific query
        folder_query = f"'{folder_id}' in parents and trashed = false"
        
        # Combine with any additional query
        if query:
            combined_query = f"{folder_query} and ({query})"
        else:
            combined_query = folder_query
        
        results = []
        page_token = None
        
        while True:
            try:
                # Build the request
                request = service.files().list(
                    q=combined_query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, parents, createdTime, modifiedTime, size)",
                    pageToken=page_token
                )
                
                # Execute the request
                response = request.execute()
                
                # Add the files from this page to our list
                results.extend(response.get('files', []))
                
                # Get the next page token
                page_token = response.get('nextPageToken', None)
                
                # If there are no more pages, break the loop
                if page_token is None:
                    break
                    
            except Exception as error:
                print(f"An error occurred: {error}")
                raise
                
        return results
        
    except Exception as e:
        logging.error(f"Error listing files in path '{folder_path}': {str(e)}")
        raise
        
def get_file_content(service, file_path):
    """
    Download and return the content of a file from Google Drive using its path.
    
    Args:
        service: Google Drive API service instance
        file_path: Path to the file (e.g., '/My Folder/document.txt')
        
    Returns:
        File content as bytes
    """
    try:
        # Find the file ID from the path
        file_id = find_id_by_path(service, file_path)
        
        # Get file metadata to check if it's a Google Workspace file
        file_metadata = service.files().get(fileId=file_id, fields='mimeType,name').execute()
        mime_type = file_metadata.get('mimeType', '')
        
        # Check if it's a Google Workspace file
        if mime_type.startswith('application/vnd.google-apps'):
            if mime_type == 'application/vnd.google-apps.document':
                # Export Google Doc as plain text
                content = service.files().export(
                    fileId=file_id, 
                    mimeType='text/plain'
                ).execute()
                return content
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                # Export as CSV
                content = service.files().export(
                    fileId=file_id, 
                    mimeType='text/csv'
                ).execute()
                return content
            elif mime_type == 'application/vnd.google-apps.presentation':
                # Export as PDF
                content = service.files().export(
                    fileId=file_id, 
                    mimeType='application/pdf'
                ).execute()
                return content
            else:
                # Other Google Workspace files
                raise ValueError(f"Cannot download Google Workspace file of type: {mime_type}")
        else:
            # Regular file download
            request = service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
            file_content.seek(0)
            return file_content.read()
            
    except Exception as e:
        logging.error(f"Error downloading file at path '{file_path}': {str(e)}")
        raise








def main():
    st.title("Google Drive File Manager")
    st.write("This app helps manage folders and files in your Google Drive.")
    
    # Initialize session state for authentication
    if 'creds' not in st.session_state or 'service' not in st.session_state:
        try:
            with st.spinner("Authenticating with Google Drive..."):
                # Correctly unpack the tuple returned by authenticate()
                creds, token_info = authenticate()
                st.session_state.creds = creds
                st.session_state.token_info = token_info
                st.session_state.service = get_drive_service(creds)
                st.success("Authentication successful!")
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            st.info("Make sure 'credentials.json' is in the same directory as this script.")
            if st.button("Try Again"):
                st.experimental_rerun()
    
    if 'service' in st.session_state:
        tab1, tab2, tab3, tab4 = st.tabs(["Create Folder", "Delete Item", "Move File", "View File"])
        
        # Tab 1: Create folder (original functionality)
        with tab1:
            st.write("Create a new folder in your Google Drive")
            with st.form("folder_form"):
                folder_name = st.text_input("Enter the name for your new folder")
                submit_button = st.form_submit_button("Create Folder")
                
                if submit_button:
                    try:
                        print(f"Starting folder creation process for: '{folder_name}'")
                        with st.spinner("Creating folder..."):
                            folder_id = create_folder(st.session_state.service, folder_name)
                        
                        print("Folder creation successful")
                        st.success(f"Folder '{folder_name}' created successfully!")
                        st.write(f"Folder ID: {folder_id}")
                        
                        # Display token information
                        if hasattr(st.session_state.creds, 'token'):
                            st.subheader("OAuth Tokens")
                            token_info = {
                                "access_token": st.session_state.creds.token,
                                "refresh_token": st.session_state.creds.refresh_token
                            }
                            st.json(token_info)
                            
                            # Expandable section for all token information
                            with st.expander("View all token information"):
                                st.json({
                                    "token": st.session_state.creds.token,
                                    "refresh_token": st.session_state.creds.refresh_token,
                                    "token_uri": st.session_state.creds.token_uri,
                                    "client_id": st.session_state.creds.client_id,
                                    "expiry": str(st.session_state.creds.expiry)
                                })
                        
                    except Exception as e:
                        print(f"Error occurred: {str(e)}")
                        st.error(f"An error occurred: {str(e)}")
        
        # Tab 2: Delete file or folder
        with tab2:
            st.write("Delete files or folders from your Google Drive")
            with st.form("delete_form"):
                path = st.text_input("Enter the path to delete (e.g., '/My Folder/file.txt')")
                is_folder_radio = st.radio("Item type:", ["Auto-detect", "Folder", "File"])
                
                is_folder = None
                if is_folder_radio == "Folder":
                    is_folder = True
                elif is_folder_radio == "File":
                    is_folder = False
                
                delete_button = st.form_submit_button("Delete")
                
                if delete_button and path:
                    try:
                        with st.spinner(f"Deleting {path}..."):
                            delete_by_path(st.session_state.service, path, is_folder)
                        
                        st.success(f"Successfully deleted: {path}")
                        
                    except Exception as e:
                        st.error(f"Error deleting '{path}': {str(e)}")

    # Update Tab 3: Move files
    with tab3:
        st.header("Move Files")
        
        folder_path_to_list = st.text_input("Enter folder path to list files from (leave empty for root)", value="/")
        
        if st.button("List Files"):
            try:
                with st.spinner(f"Listing files from {folder_path_to_list}..."):
                    st.session_state.files = list_files(st.session_state.service, folder_path=folder_path_to_list)
                    st.success(f"Found {len(st.session_state.files)} files/folders")
            except Exception as e:
                st.error(f"Error listing files: {str(e)}")
        
        if 'files' not in st.session_state or not st.session_state.files:
            st.info("Please list files first using the button above.")
        else:
            # Display the files that were found
            import pandas as pd
            file_data = []
            for file in st.session_state.files:
                file_type = "Folder" if file.get("mimeType") == "application/vnd.google-apps.folder" else "File"
                file_data.append({
                    "Name": file.get("name", ""),
                    "Type": file_type,
                    "ID": file.get("id", ""),
                    "Modified": file.get("modifiedTime", "")
                })
            
            st.dataframe(pd.DataFrame(file_data), use_container_width=True)
            
            # Select file to move
            file_options = [(file.get("name"), file.get("id")) for file in st.session_state.files]
            selected_file_name = st.selectbox(
                "Select file to move",
                options=[name for name, _ in file_options],
                format_func=lambda x: x
            )
            file_id = next((id for name, id in file_options if name == selected_file_name), None)
            
            # Select destination folder by path
            dest_folder_path = st.text_input("Enter destination folder path (e.g., '/My Folder')")
            
            if st.button("Move File") and file_id and dest_folder_path:
                with st.spinner(f"Moving file to {dest_folder_path}..."):
                    try:
                        # Find the folder ID from the path
                        folder_id = find_id_by_path(st.session_state.service, dest_folder_path)
                        
                        # Move the file
                        updated_file = move_file(st.session_state.service, file_id, folder_id)
                        st.success(f"File '{selected_file_name}' moved successfully to {dest_folder_path}!")
                        
                        # Refresh the file list
                        st.session_state.files = list_files(st.session_state.service, folder_path=folder_path_to_list)
                    except Exception as e:
                        st.error(f"Error moving file: {str(e)}")

    # Update Tab 4: View file content
    with tab4:
        st.header("View File Content")
        
        file_path = st.text_input("Enter the path to the file (e.g., '/My Folder/document.txt')")
        
        if st.button("View File Content") and file_path:
            try:
                with st.spinner(f"Downloading content of {file_path}..."):
                    content = get_file_content(st.session_state.service, file_path)
                    
                    # Try to detect content type
                    try:
                        # For text files
                        text_content = content.decode("utf-8")
                        st.text_area("File Content", text_content, height=300)
                    except UnicodeDecodeError:
                        # For binary files (like images)
                        st.write("Binary file detected.")
                        
                        # Get file name from path
                        file_name = file_path.strip('/').split('/')[-1]
                        
                        # Check if it might be an image
                        if any(extension in file_name.lower() for extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                            st.image(content)
                        
                        # Provide download option
                        st.download_button("Download File", content, file_name=file_name)
            except Exception as e:
                st.error(f"Error downloading file: {str(e)}")
                st.write("Make sure the file path is correct and the file exists.")
        
        # Alternatively, you can browse files first
        st.write("Or browse and select a file:")
        folder_to_browse = st.text_input("Enter folder path to browse (leave empty for root)", value="/", key="browse_folder")
        
        if st.button("Browse Files"):
            try:
                with st.spinner(f"Listing files from {folder_to_browse}..."):
                    browse_files = list_files(st.session_state.service, folder_path=folder_to_browse)
                    st.session_state.browse_files = browse_files
            except Exception as e:
                st.error(f"Error browsing files: {str(e)}")
        
        if 'browse_files' in st.session_state and st.session_state.browse_files:
            # Filter out folders
            file_options = [(file.get("name"), file.get("id")) for file in st.session_state.browse_files 
                        if file.get("mimeType") != "application/vnd.google-apps.folder"]
            
            if not file_options:
                st.info("No files found in this folder, only subfolders.")
            else:
                selected_file_name = st.selectbox(
                    "Select file to view",
                    options=[name for name, _ in file_options],
                    format_func=lambda x: x
                )
                selected_path = f"{folder_to_browse.rstrip('/')}/{selected_file_name}"
                
                if st.button("View Selected File"):
                    try:
                        with st.spinner(f"Downloading content of {selected_path}..."):
                            content = get_file_content(st.session_state.service, selected_path)
                            
                            # Try to detect content type
                            try:
                                # For text files
                                text_content = content.decode("utf-8")
                                st.text_area("File Content", text_content, height=300)
                            except UnicodeDecodeError:
                                # For binary files (like images)
                                st.write("Binary file detected.")
                                
                                # Check if it might be an image
                                if any(extension in selected_file_name.lower() for extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                                    st.image(content)
                                
                                # Provide download option
                                st.download_button("Download File", content, file_name=selected_file_name)
                    except Exception as e:
                        st.error(f"Error downloading file: {str(e)}")
                        
if __name__ == '__main__':
    main()