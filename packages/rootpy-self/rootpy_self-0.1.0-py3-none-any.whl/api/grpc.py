import requests

from ..constants import API_BASE, USER_AGENT
from ..proto import encode_grpc_web_message


class GrpcClient:
    def __init__(self, token):
        self.token = token
        self.session = requests.Session()
        
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)

        self.headers = {
            "content-type": "application/grpc-web",
            "user-agent": USER_AGENT,
            "te": "trailers",
            "grpc-accept-encoding": "identity,gzip,deflate",
            "authorization": f"Bearer {token}",
        }

    def request(self, endpoint, payload=b""):
        url = f"{API_BASE}/{endpoint}"
        return self.session.post(
            url, 
            data=encode_grpc_web_message(payload), 
            headers=self.headers, 
            timeout=30
        )
