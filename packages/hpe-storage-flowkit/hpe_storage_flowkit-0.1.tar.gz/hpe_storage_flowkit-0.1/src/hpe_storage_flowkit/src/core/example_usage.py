from hpe_storage_flowkit.src.core.rest_client import RESTClient
from hpe_storage_flowkit.src.core.session import SessionManager

api_url = "https://your-3par-api-url"
username = "admin"
password = "yourpassword"

# REST client usage
rest_client = RESTClient(api_url, username, password)
volumes = rest_client.get("/volumes")
print("Volumes:", volumes)

# Session manager usage
session_mgr = SessionManager(api_url, username, password)
token = session_mgr.login()
print("Session token:", token)
