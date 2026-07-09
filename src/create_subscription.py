import json
import requests

ORION = "http://127.0.0.1:1026"

HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/ld+json"
}

with open("subscription-ql-ngsild-normalized.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

r = requests.post(
    f"{ORION}/ngsi-ld/v1/subscriptions",
    json=payload,
    headers=HEADERS,
    timeout=10
)

print(r.status_code)
print(r.text)