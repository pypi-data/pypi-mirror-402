from hpe_storage_flowkit.src.core.session import SessionManager

api_url = "https://your-3par-api-url"
username = "admin"
password = "yourpassword"

# Initialize session manager
session_mgr = SessionManager(api_url, username, password)

# Login and get token
print("Logging in...")
token = session_mgr.login()
print("Session token:", token)

# Ensure session (will return token, login if needed)
print("Ensuring session...")
token2 = session_mgr.ensure_session()
print("Ensured session token:", token2)

# Use session_mgr.get_token() to get the current token
print("Current token:", session_mgr.get_token())

# Delete session
print("Deleting session...")
session_mgr.delete_session()
print("Session deleted.")
