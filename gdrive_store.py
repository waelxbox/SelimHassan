import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
# SWAPPED THIS IMPORT:
from google.oauth2.credentials import Credentials

class GDriveStore:
    def __init__(self, credentials_info):
        # SWAPPED THIS AUTHENTICATION METHOD:
        self.creds = Credentials.from_authorized_user_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        
        # Keep your hardcoded Root ID!
        self.root_id = "1lTRwzaW646YNw1Q9A9sqacOO00E1BIYw"
        self.uploads_folder_name = "scans"
        self.transcriptions_folder_name = "transcriptions"
        
        self._ensure_folders()
        
    # ... keep all other functions exactly the same ...

    def _ensure_folders(self):
        """Ensures the folder structure exists in Google Drive."""
        # Notice we removed the line that tries to create the root folder!
        self.uploads_id = self._get_or_create_folder(self.uploads_folder_name, self.root_id)
        self.transcriptions_id = self._get_or_create_folder(self.transcriptions_folder_name, self.root_id)

    def _get_or_create_folder(self, name, parent_id=None):
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        file = self.service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

    def list_files(self, folder_id):
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def get_file_content(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return fh.getvalue()

    def upload_file(self, name, content, folder_id, mime_type='application/octet-stream'):
        # Check if file exists to update instead of duplicate
        query = f"name = '{name}' and '{folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id)").execute()
        existing_files = results.get('files', [])

        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
        
        if existing_files:
            file_id = existing_files[0]['id']
            return self.service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {'name': name, 'parents': [folder_id]}
            return self.service.files().create(body=file_metadata, media_body=media).execute()
