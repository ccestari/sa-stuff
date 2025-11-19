import requests
import base64

client_key = "3P6juCNpC2FmH13Pq8FYeggQbY0W0Vbhssg0-8"
client_secret = "dM4tN0zeZ3d6FxA3oOg76u0Ujk0dgF01nZ02mtnP"

# Test different auth methods
auth_methods = [
    ("Basic key:", base64.b64encode(f"{client_key}:".encode()).decode()),
    ("Basic key:secret", base64.b64encode(f"{client_key}:{client_secret}".encode()).decode()),
    ("Bearer key", client_key)
]

for method, cred in auth_methods:
    headers = {"Authorization": f"Basic {cred}" if "Basic" in method else f"Bearer {cred}"}
    response = requests.get("https://harvest.greenhouse.io/v1/candidates", headers=headers)
    print(f"{method}: {response.status_code} - {response.text[:100]}")