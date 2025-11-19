import requests
import base64

client_key = "3P6juCNpC2FmH13Pq8FYeggQbY0W0Vbhssg0-8"
credentials = base64.b64encode(f"{client_key}:".encode()).decode()
headers = {"Authorization": f"Basic {credentials}"}

# Test simpler endpoints
endpoints = ["/users", "/departments", "/offices"]

for endpoint in endpoints:
    response = requests.get(f"https://harvest.greenhouse.io/v1{endpoint}", headers=headers)
    print(f"{endpoint}: {response.status_code} - {response.text[:100]}")