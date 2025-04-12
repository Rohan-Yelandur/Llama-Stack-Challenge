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
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate():
    """Authenticate with Google Drive and return credentials"""
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    st.write("Starting OAuth flow...")
    creds = flow.run_local_server(port=3000)
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


# def view_file_contents(service, file_id):
    






def find_id_by_path(service, path):
    """
    Find the file or folder ID by navigating through the path.
    
    Args:
        service: Google Drive API service instance
        path: Path in format "/folder/subfolder/file.txt" or "/folder/subfolder/"
        
    Returns:
        ID of the file or folder at the specified path
    """
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
    """
    Delete a file from Google Drive.
    
    Args:
        service: Google Drive API service instance
        file_id: ID of the file to delete
        
    Returns:
        True if deletion was successful
    """
    service.files().delete(fileId=file_id).execute()
    return True

def delete_folder(service, folder_id, recursive=True):
    """
    Delete a folder from Google Drive.
    
    Args:
        service: Google Drive API service instance
        folder_id: ID of the folder to delete
        recursive: If True, delete all contents; if False, fail if folder isn't empty
        
    Returns:
        True if deletion was successful
    """
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
    """
    Delete a file or folder by path.
    
    Args:
        service: Google Drive API service instance
        path: Path to the file or folder
        is_folder: True for folder, False for file, None for auto-detect
        
    Returns:
        True if deletion was successful
    """
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
    
    # Rest of your function remains the same
    if 'service' in st.session_state:
        tab1, tab2 = st.tabs(["Create Folder", "Delete Item"])
        
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

if __name__ == '__main__':
    main()