import hashlib
import base64
import uuid
import requests
from datetime import datetime

from ..constants import UPLOAD_URL, ROOT_VERSION


class AssetUploader:
    def __init__(self, token, device_id):
        self.token = token
        self.device_id = device_id
        self.session = requests.Session()
        
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)

    def upload_bytes(self, image_data, extension="jpg"):
        md5_hash = base64.b64encode(hashlib.md5(image_data).digest()).decode()
        sha256_hash = base64.b64encode(hashlib.sha256(image_data).digest()).decode()
        filename = f"{hashlib.md5(uuid.uuid4().bytes).hexdigest()}.{extension}"
        filename_base64 = base64.b64encode(filename.encode()).decode()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + "Z"

        headers = {
            "user-agent": ROOT_VERSION,
            "x-root-device-id": self.device_id,
            "authorization": f"Bearer {self.token}",
            "content-md5": md5_hash,
            "x-amz-meta-root-content-sha256": sha256_hash,
            "x-amz-meta-root-file-name": filename,
            "x-amz-meta-root-file-name-base64": filename_base64,
            "x-amz-meta-root-file-modification": timestamp,
        }
        
        try:
            resp = self.session.post(UPLOAD_URL, headers=headers, data=image_data, timeout=15)
            if resp.status_code == 200:
                return resp.text.strip('"')
        except:
            pass
        return None

    def upload_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                image_data = f.read()
        except:
            return None
        
        extension = file_path.rsplit(".", 1)[-1] if "." in file_path else "jpg"
        return self.upload_bytes(image_data, extension)

    def upload_url(self, url):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "png" in content_type:
                    ext = "png"
                elif "gif" in content_type:
                    ext = "gif"
                elif "webp" in content_type:
                    ext = "webp"
                else:
                    ext = "jpg"
                return self.upload_bytes(resp.content, ext)
        except:
            pass
        return None
