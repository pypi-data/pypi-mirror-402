import requests
import os

class CheckpasteClient:
    def __init__(self, host: str, port: int = 8000):
        self.base_url = f"http://{host}:{port}"

    def get_clipboard(self):
        try:
            response = requests.get(f"{self.base_url}/clipboard")
            response.raise_for_status()
            return response.json().get("text", "")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")
            return None

    def send_clipboard(self, text: str):
        try:
            response = requests.post(f"{self.base_url}/clipboard", json={"text": text})
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending text to server: {e}")
            return False

    def send_file(self, file_path: str, progress_callback=None):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Generator to read file in chunks and update progress
        def file_generator(f):
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                if progress_callback:
                    progress_callback(len(chunk))
                yield chunk

        try:
            with open(file_path, 'rb') as f:
                 # Note: standard requests with a generator sets Transfer-Encoding: chunked,
                 # which FastAPI/Uvicorn supports. 
                 # However, we need to send it as multipart/form-data for UploadFile compatibility
                 # or simply use the generator as the 'files' value if requests supports it.
                 # 'requests' doesn't support streaming multipart uploads natively with a generator easily without 'toolbelt'.
                 # Fallback: For MVP without adding dependencies, we'll keep it simple:
                 # If we want a progress bar, we essentially need 'requests-toolbelt' for MultipartEncoderMonitor.
                 # OR we can just upload the file object (which requests streams) but we won't get a callback *during* the read easily.
                 # Let's use a simpler approach: Just rely on requests streaming (it does lazily read file objects).
                 # To get a Progress Bar, we can wrap the file object.
                 
                 class ProgressFile:
                    def __init__(self, file_path, callback):
                        self.f = open(file_path, "rb")
                        self.callback = callback
                        self.len = os.path.getsize(file_path)
                    
                    def __len__(self):
                        return self.len

                    def read(self, size=-1):
                        chunk = self.f.read(size)
                        if self.callback:
                            self.callback(len(chunk))
                        return chunk
                        
                    def close(self):
                        self.f.close()

                 wrapped_file = ProgressFile(file_path, progress_callback)
                 
                 files = {'file': (filename, wrapped_file, 'application/octet-stream')}
                 response = requests.post(f"{self.base_url}/file", files=files)
                 wrapped_file.close() # Ensure close
                 
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending file: {e}")
            return False

    def download_file(self, filename: str, destination: str = None):
        url = f"{self.base_url}/file/{filename}"
        local_filename = destination or filename
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return local_filename
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return None

    def list_files(self):
        try:
            response = requests.get(f"{self.base_url}/files")
            response.raise_for_status()
            return response.json().get("files", [])
        except requests.exceptions.RequestException as e:
            print(f"Error listing files: {e}")
            return []
