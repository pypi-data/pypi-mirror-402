from hpe_storage_flowkit.src.core.rest_client import RESTClient

api_url = "https://your-3par-api-url"
username = "admin"
password = "yourpassword"

# Initialize REST client (performs login and stores token)
rest_client = RESTClient(api_url, username, password)

# Example: GET request to list volumes
try:
    volumes = rest_client.get("/volumes")
    print("Volumes:", volumes)
except Exception as e:
    print("Error fetching volumes:", e)

# Example: POST request to create a volume
volume_payload = {
    "name": "vol_test",
    "sizeMiB": 1024,
    "cpg": "CPG1"
}
try:
    response = rest_client.post("/volumes", payload=volume_payload)
    print("Volume creation response:", response)
except Exception as e:
    print("Error creating volume:", e)

# Example: DELETE request to delete a volume
try:
    response = rest_client.delete("/volumes/vol_test")
    print("Volume deletion response:", response)
except Exception as e:
    print("Error deleting volume:", e)

# Example: Set a custom header
rest_client.set_header("X-Custom-Header", "value123")
print("Custom header set.")

# Example: Remove a custom header
rest_client.remove_header("X-Custom-Header")
print("Custom header removed.")
