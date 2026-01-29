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

    def send_file(self, file_path: str):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        try:
            files = {'file': open(file_path, 'rb')}
            response = requests.post(f"{self.base_url}/file", files=files)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending file: {e}")
            return False
