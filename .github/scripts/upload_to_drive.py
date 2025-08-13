import os
import sys
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_drive(file_path):
    # Load credentials from GitHub secrets
    creds_info = json.loads(os.environ['GDRIVE_CREDENTIALS'])
    token_info = json.loads(os.environ['GDRIVE_TOKEN'])
    
    creds = Credentials.from_authorized_user_info(token_info)
    service = build('drive', 'v3', credentials=creds)
    
    # Check if file already exists
    file_name = "Umbra-Project-Live-Docs.md"
    existing_files = service.files().list(
        q=f"name='{file_name}'",
        spaces='drive'
    ).execute()
    
    media = MediaFileUpload(file_path, mimetype='text/markdown')
    
    if existing_files['files']:
        # Update existing file
        file_id = existing_files['files'][0]['id']
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"Updated file: {file_name}")
    else:
        # Create new file
        file_metadata = {'name': file_name}
        service.files().create(
            body=file_metadata,
            media_body=media
        ).execute()
        print(f"Created file: {file_name}")

if __name__ == "__main__":
    upload_to_drive(sys.argv[21])
