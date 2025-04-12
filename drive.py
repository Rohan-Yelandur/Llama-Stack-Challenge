import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def create_folder(folder_name):
    """Create a folder in Google Drive and return its ID and tokens."""
    # Start the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    print("Starting OAuth flow on port 3000...")
    st.write("Starting OAuth flow...")
    creds = flow.run_local_server(port=3000)  # Changed port to avoid conflict with Streamlit
    print(f"OAuth completed. Access token: {creds.token[:10]}...")
    
    # Get tokens
    token_info = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    
    print(f"Tokens received: {json.dumps(token_info, indent=2)}")
    
    # Build the Drive API service
    print("Building Drive API service...")
    service = build('drive', 'v3', credentials=creds)
    
    # Create a folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    print(f"Making API request to create folder: {json.dumps(folder_metadata, indent=2)}")
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    print(f"API response: {json.dumps(folder, indent=2)}")
    
    folder_id = folder.get('id')
    print(f"Folder created with ID: {folder_id}")
    
    return folder_id, token_info

def main():
    st.title("Google Drive Folder Creator")
    st.write("This app creates a folder in your Google Drive and displays your OAuth tokens.")
    
    with st.form("folder_form"):
        folder_name = st.text_input("Enter the name for your new folder")
        submit_button = st.form_submit_button("Create Folder")
        
        if submit_button:
            try:
                print(f"Starting folder creation process for: '{folder_name}'")
                with st.spinner("Authenticating with Google and creating folder..."):
                    folder_id, token_info = create_folder(folder_name)
                
                print("Folder creation successful")
                st.success(f"Folder '{folder_name}' created successfully!")
                st.write(f"Folder ID: {folder_id}")
                
                # Display tokens
                st.subheader("OAuth Tokens")
                st.json({
                    "access_token": token_info["access_token"],
                    "refresh_token": token_info["refresh_token"]
                })
                
                # Expandable section for all token information
                with st.expander("View all token information"):
                    st.json(token_info)
                    
            except Exception as e:
                print(f"Error occurred: {str(e)}")
                st.error(f"An error occurred: {str(e)}")
                st.info("Make sure 'credentials.json' is in the same directory as this script.")

if __name__ == '__main__':
    main()